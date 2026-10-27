"""
apps/api/app/agent/state_machine.py — Single-Execution Bounded Investigation Orchestrator

Design:
1. One-click / one-call produces exactly one execution bound to the given case.
2. Returns a run ID immediately.
3. Background task executes the 8 stages with bounded wall-clock, token, and step budgets.
4. Server-Sent Events (SSE) observe the existing run and replay past events on reconnect.
5. Never hardcodes any case ID; fully bound to the target case.
6. Reconnecting to SSE is idempotent and never triggers duplicate model or provider calls.
7. Explicit failure, timeout, and cancellation handling.
"""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from ..config import settings
from ..domain.detector import DeterministicExcursionEngine, format_iso_utc
from ..domain.models import (
    AgentState,
    InvestigationRun,
    ShipmentCase,
    ToolEvent,
)
from ..domain.validator import ClaimsValidator
from ..providers.nebius import NebiusTokenFactoryProvider
from ..providers.tavily import TavilySearchProvider


class InvestigationOrchestrator:
    def __init__(self):
        self.detector = DeterministicExcursionEngine()
        self.validator = ClaimsValidator()
        self.tavily = TavilySearchProvider(
            api_key=settings.tavily_key,
            app_mode=settings.app_mode
        )
        self.nebius = NebiusTokenFactoryProvider(
            api_key=settings.nebius_key,
            base_url=settings.nebius_base_url,
            fast_model_id=settings.nvidia_fast_model_id,
            deep_model_id=settings.nvidia_deep_model_id,
            app_mode=settings.app_mode
        )
        # In-memory execution registry
        self.runs: dict[str, InvestigationRun] = {}
        self.cases: dict[str, ShipmentCase] = {}
        self.event_buffers: dict[str, list[dict[str, Any]]] = {}
        self.listeners: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self.tasks: dict[str, asyncio.Task[Any]] = {}

    def get_run(self, run_id: str) -> InvestigationRun | None:
        return self.runs.get(run_id)

    def _prune_old_runs(self, max_runs: int = 100):
        """Keeps in-memory storage bounded by pruning oldest terminal runs."""
        if len(self.runs) <= max_runs:
            return
        removable = [
            rid for rid, r in self.runs.items()
            if r.state in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY")
        ]
        for rid in removable[: len(self.runs) - max_runs]:
            self.runs.pop(rid, None)
            self.cases.pop(rid, None)
            self.event_buffers.pop(rid, None)
            self.listeners.pop(rid, None)
            self.tasks.pop(rid, None)

    def init_run(self, case: ShipmentCase, run_id: str | None = None) -> str:
        """Initializes run record, event buffer and listener registry."""
        self._prune_old_runs()
        rid = run_id or f"RUN-{uuid.uuid4().hex[:8]}"

        run = InvestigationRun(
            id=rid,
            case_id=case.id,
            state="CREATED",
            created_at=format_iso_utc(datetime.now(UTC)),
            provider_mode="DEMO_FIXTURE",
            requested_model=settings.nvidia_deep_model_id,
            served_model=None,
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            tool_events=[]
        )

        self.runs[rid] = run
        self.cases[rid] = case
        self.event_buffers[rid] = []
        self.listeners[rid] = []
        return rid

    async def execute_run_background(self, run_id: str, case: ShipmentCase):
        """Entry point for background task execution without request scope cancellation."""
        task = asyncio.current_task()
        if task:
            self.tasks[run_id] = task
        await self._execute_run(run_id, case)

    def start_investigation(self, case: ShipmentCase, run_id: str | None = None) -> str:
        """Creates exactly one investigation run, returns its ID immediately, and launches execution in background."""
        rid = self.init_run(case, run_id)
        task = asyncio.create_task(self._execute_run(rid, case))
        self.tasks[rid] = task
        return rid

    async def wait_for_completion(self, run_id: str, timeout: float = 10.0) -> InvestigationRun:
        """Awaits until run reaches a terminal state (HUMAN_REVIEW_READY or FAILED_TRUTHFULLY)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            run = self.runs.get(run_id)
            if run and run.state in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
                return run
            await asyncio.sleep(0.02)
        return self.runs[run_id]

    def _broadcast_event(self, run_id: str, event_data: dict[str, Any]):
        """Records event with monotonic sequence in run history and pushes to active listener queues."""
        if run_id not in self.event_buffers:
            self.event_buffers[run_id] = []

        seq = len(self.event_buffers[run_id]) + 1
        event_data["seq"] = seq
        self.event_buffers[run_id].append(event_data)

        if run_id in self.listeners:
            for q in list(self.listeners[run_id]):
                try:
                    q.put_nowait(event_data)
                except Exception:
                    pass

    async def _execute_run(self, run_id: str, case: ShipmentCase):
        """Executes the 8-stage pipeline once within bounded wall-clock budget and async timeouts."""
        run = self.runs[run_id]
        start_time = time.time()

        def emit(stage: AgentState, message: str, data: dict[str, Any] | None = None):
            run.state = stage
            evt = ToolEvent(
                timestamp=format_iso_utc(datetime.now(UTC)),
                tool_name=stage,
                status="SUCCESS" if stage != "FAILED_TRUTHFULLY" else "FAILED",
                summary=message
            )
            run.tool_events.append(evt)
            event_obj = {
                "event": "stage_update",
                "run_id": run_id,
                "stage": stage,
                "message": message,
                "data": data or {},
                "run": run.model_dump()
            }
            self._broadcast_event(run_id, event_obj)

        try:
            # Enforce bounded investigation timeout
            timeout_limit = float(settings.investigation_timeout_seconds)
            async with asyncio.timeout(timeout_limit):
                emit("CREATED", f"Investigation initialized for case {case.id}")
                await asyncio.sleep(0.05)

                # 1. VALIDATING
                emit("VALIDATING", "Validating case schema and reading bounds")
                if not case.readings or len(case.readings) < 1:
                    run.state = "FAILED_TRUTHFULLY"
                    run.failure_reason = "Case contains 0 sensor readings."
                    emit("FAILED_TRUTHFULLY", run.failure_reason)
                    return

                # 2. NORMALIZING
                emit("NORMALIZING", "Normalizing time-series timestamps and telemetry points")
                await asyncio.sleep(0.05)

                # 3. DETECT_EXCURSION (Deterministic multi-sensor analysis)
                analysis = self.detector.analyze_case(case)
                run.observations = analysis.observations

                excursion_summary = (
                    f"Detected {analysis.total_excursion_duration_minutes:.1f} minutes cumulative excursion. "
                    f"Max temp: {analysis.max_recorded_temperature:.1f}°C."
                    if analysis.has_excursion else "No excursion was detected in the supplied telemetry; all readings within configured temperature band."
                )
                emit("EXCURSION_DETECTED", excursion_summary, {
                    "has_excursion": analysis.has_excursion,
                    "duration_minutes": analysis.total_excursion_duration_minutes,
                    "max_temperature": analysis.max_recorded_temperature,
                    "observations_count": len(analysis.observations)
                })
                await asyncio.sleep(0.05)

                # 4. RESEARCHING (Tavily Async)
                query = f"CDC FDA cold chain vaccine temperature excursion guidance for {case.product_profile.product_class}"
                emit("RESEARCHING", f"Querying authoritative guidance via Tavily: '{query}'")

                sources, tavily_receipt = await self.tavily.search_guidance_async(query, max_results=3)
                run.sources = sources
                tavily_is_live = bool(tavily_receipt.get("is_live", False))

                emit("RESEARCHING", f"Retrieved {len(sources)} authoritative source records from CDC/FDA/WHO/GS1", {
                    "source_count": len(sources),
                    "tavily_receipt": tavily_receipt
                })
                await asyncio.sleep(0.05)

                # Discover key-scoped Nebius model catalog before investigator execution
                selected_runtime_model: str | None = None
                catalog_probe: dict[str, Any] = {}
                if self.nebius.has_key:
                    catalog_probe = await self.nebius.discover_models_async()
                    if catalog_probe.get("status") == "LIVE_SUCCESS":
                        selected_runtime_model = catalog_probe.get("selected_deep_model")

                # 5. HYPOTHESES_DRAFTED (Nebius Async + NVIDIA Nemotron)
                emit("HYPOTHESES_DRAFTED", "Synthesizing competing causal hypotheses via NVIDIA Nemotron")
                hypotheses, nebius_receipt = await self.nebius.generate_hypotheses_async(
                    case,
                    run.observations,
                    run.sources,
                    model_override=selected_runtime_model
                )
                run.hypotheses = hypotheses
                run.latency_ms = nebius_receipt.get("latency_ms")
                run.usage = nebius_receipt.get("usage")
                investigator_is_live = bool(nebius_receipt.get("is_live", False))

                emit("HYPOTHESES_DRAFTED", f"Drafted {len(hypotheses)} competing causal hypotheses", {
                    "hypotheses_count": len(hypotheses),
                    "nebius_receipt": nebius_receipt
                })
                await asyncio.sleep(0.05)

                # 6. SKEPTIC_REVIEWED (Nebius Async)
                emit("SKEPTIC_REVIEWED", "Running adversarial skeptic pass to identify contradictions and overclaims")
                critiques, skeptic_receipt = await self.nebius.run_skeptic_pass_async(
                    run.hypotheses,
                    run.observations,
                    run.sources,
                    model_override=selected_runtime_model
                )
                run.critiques = critiques
                skeptic_is_live = bool(skeptic_receipt.get("is_live", False))

                # Update hypothesis status from skeptic recommendation
                for c in critiques:
                    for h in run.hypotheses:
                        if h.id == c.hypothesis_id:
                            h.status = c.recommended_status

                emit("SKEPTIC_REVIEWED", f"Completed skeptic pass: {len(critiques)} critiques evaluated", {
                    "critique_count": len(critiques),
                    "skeptic_receipt": skeptic_receipt
                })
                await asyncio.sleep(0.05)

                # 7. CLAIMS_VALIDATED
                emit("CLAIMS_VALIDATED", "Validating hypothesis claims and citations deterministically")

                # Check 1: validate_hypotheses
                is_valid, validation_errors = self.validator.validate_hypotheses(
                    run.hypotheses,
                    run.observations,
                    run.sources
                )

                # Check 2: validate_skeptic_critiques (verifying coverage across all hypotheses)
                if is_valid:
                    critiques_valid, c_errors = self.validator.validate_skeptic_critiques(
                        run.critiques,
                        hypotheses=run.hypotheses
                    )
                    if not critiques_valid:
                        is_valid = False
                        validation_errors.extend(c_errors)

                # Check 3: inspect_complete_run
                if is_valid:
                    run_valid, r_errors = self.validator.inspect_complete_run(run.model_dump())
                    if not run_valid:
                        is_valid = False
                        validation_errors.extend(r_errors)

                run.validation_result = {
                    "passed": is_valid,
                    "error_count": len(validation_errors),
                    "errors": validation_errors
                }

                if not is_valid:
                    run.state = "FAILED_TRUTHFULLY"
                    run.failure_reason = "Claims validator failed: " + "; ".join(validation_errors)
                    emit("FAILED_TRUTHFULLY", run.failure_reason)
                    return

                emit("CLAIMS_VALIDATED", "Citation IDs and prohibited-claim rules passed deterministic validation.")
                await asyncio.sleep(0.05)

                # Determine truthful overall provider mode (Section 2A fail-closed requirements):
                # A run may be labeled LIVE_TOKEN_FACTORY only if ALL of these succeeded during that exact run:
                # 1. Nebius credentials authenticated
                # 2. Nebius GET /models succeeded
                # 3. Catalog contained an eligible NVIDIA/Nemotron model
                # 4. The exact served model is present in that returned catalog
                # 5. Investigator inference succeeded live
                # 6. Skeptic inference succeeded live
                # 7. Tavily retrieval succeeded live
                # 8. Tavily returned at least one valid allowlisted source
                # 9. Provider response schemas passed
                # 10. Claims validation passed
                allowlisted_domains = {"cdc.gov", "fda.gov", "who.int", "gs1.org", "usp.org"}
                served_model_name = nebius_receipt.get("model", "")
                catalog_models = set(catalog_probe.get("nvidia_models", []))

                is_live_catalog_ok = (
                    catalog_probe.get("status") == "LIVE_SUCCESS"
                    and len(catalog_models) > 0
                    and served_model_name in catalog_models
                )
                is_live_investigator_ok = (
                    investigator_is_live
                    and nebius_receipt.get("status") == "LIVE_SUCCESS"
                    and bool(nebius_receipt.get("response_digest"))
                )
                is_live_skeptic_ok = (
                    skeptic_is_live
                    and skeptic_receipt.get("status") == "LIVE_SUCCESS"
                    and bool(skeptic_receipt.get("response_digest"))
                )
                is_live_tavily_ok = (
                    tavily_is_live
                    and tavily_receipt.get("status") == "LIVE_SUCCESS"
                    and len(run.sources) > 0
                    and all(s.domain.lower() in allowlisted_domains for s in run.sources)
                )
                has_valid_schemas = len(run.hypotheses) > 0 and len(run.critiques) > 0

                can_be_live = (
                    self.nebius.has_key
                    and self.tavily.has_key
                    and is_live_catalog_ok
                    and is_live_investigator_ok
                    and is_live_skeptic_ok
                    and is_live_tavily_ok
                    and has_valid_schemas
                    and is_valid
                )

                if can_be_live:
                    run.provider_mode = "LIVE_TOKEN_FACTORY"
                    run.served_model = served_model_name
                elif self.nebius.has_key or self.tavily.has_key:
                    run.provider_mode = "DEMO_FIXTURE_FALLBACK"
                    run.served_model = f"{selected_runtime_model or settings.nvidia_deep_model_id} (fixture fallback)"
                else:
                    run.provider_mode = "DEMO_FIXTURE"
                    run.served_model = f"{settings.nvidia_deep_model_id} (synthetic fixture)"

                # 8. HUMAN_REVIEW_READY
                run.completed_at = format_iso_utc(datetime.now(UTC))
                run.state = "HUMAN_REVIEW_READY"
                run.review_posture = "QUARANTINE_PENDING_QUALIFIED_REVIEW" if analysis.has_excursion else "REQUEST_ADDITIONAL_EVIDENCE"

                total_latency = int((time.time() - start_time) * 1000)
                run.latency_ms = total_latency

                emit("HUMAN_REVIEW_READY", f"Investigation complete in {total_latency}ms. Posture: {run.review_posture}", {
                    "review_posture": run.review_posture,
                    "total_latency_ms": total_latency,
                    "provider_mode": run.provider_mode,
                    "completed_run": run.model_dump()
                })

        except TimeoutError:
            run.state = "FAILED_TRUTHFULLY"
            run.failure_reason = f"Investigation exceeded configured timeout limit of {settings.investigation_timeout_seconds}s."
            emit("FAILED_TRUTHFULLY", run.failure_reason)
        except asyncio.CancelledError:
            run.state = "FAILED_TRUTHFULLY"
            run.failure_reason = "Investigation was cancelled by user."
            emit("FAILED_TRUTHFULLY", "Investigation cancelled.")
        except Exception as e:
            run.state = "FAILED_TRUTHFULLY"
            run.failure_reason = f"Investigation exception: {type(e).__name__} - {e}"
            emit("FAILED_TRUTHFULLY", run.failure_reason)

    async def subscribe(self, run_id: str) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribes to an investigation's event stream without race conditions. Replays buffered past events and streams live ones."""
        if run_id not in self.runs:
            raise KeyError(f"Run ID '{run_id}' not found.")

        # 1. Register queue for new events BEFORE taking past events snapshot to prevent missed-event races
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        if run_id not in self.listeners:
            self.listeners[run_id] = []
        self.listeners[run_id].append(queue)

        last_seq_yielded = 0
        try:
            # 2. Yield all previously buffered events up to snapshot
            past_events = list(self.event_buffers.get(run_id, []))
            for evt in past_events:
                seq = evt.get("seq", 0)
                if seq > last_seq_yielded:
                    last_seq_yielded = seq
                yield evt

            # If already completed or failed, drain remaining items and finish
            run = self.runs[run_id]
            if run.state in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
                while not queue.empty():
                    evt = queue.get_nowait()
                    seq = evt.get("seq", 0)
                    if seq > last_seq_yielded:
                        last_seq_yielded = seq
                        yield evt
                return

            # 3. Stream new events, deduplicating against replayed sequence numbers
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                seq = event.get("seq", 0)
                if seq > last_seq_yielded:
                    last_seq_yielded = seq
                    yield event

                stage = event.get("stage")
                if stage in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
                    break
        except (TimeoutError, asyncio.CancelledError):
            pass
        finally:
            if run_id in self.listeners and queue in self.listeners[run_id]:
                self.listeners[run_id].remove(queue)

    def cancel_investigation(self, run_id: str) -> bool:
        """Cancels a running investigation task and preserves FAILED_TRUTHFULLY terminal state."""
        task = self.tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            run = self.runs.get(run_id)
            if run and run.state not in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
                run.state = "FAILED_TRUTHFULLY"
                run.failure_reason = "Investigation was cancelled by user."
            return True
        return False
