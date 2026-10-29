"""
apps/api/tests/test_orchestrator_deep_coverage.py — Tests for Orchestrator Cancellation, Pruning & Event Streaming
"""

import asyncio

import pytest
from apps.api.app.agent.state_machine import InvestigationOrchestrator
from apps.api.app.domain.models import InvestigationRun, ShipmentCase
from apps.api.app.main import CASES_STORE, load_default_fixtures


@pytest.fixture(autouse=True)
def ensure_fixtures():
    load_default_fixtures()


@pytest.fixture
def orchestrator():
    return InvestigationOrchestrator()


def test_prune_old_runs(orchestrator):
    # Add 150 terminal runs
    for i in range(150):
        run = InvestigationRun(
            id=f"RUN-PRUNE-{i:03d}",
            case_id="CASE-NMB-204",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-21T10:00:00Z",
            provider_mode="DEMO_FIXTURE",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
            disclaimer="Test",
        )
        orchestrator.runs[run.id] = run

    assert len(orchestrator.runs) == 150
    orchestrator._prune_old_runs(max_runs=100)
    assert len(orchestrator.runs) <= 100


@pytest.mark.asyncio
async def test_cancel_investigation_success_and_not_found(orchestrator):
    # 1. Non-existent run
    assert orchestrator.cancel_investigation("NON-EXISTENT") is False

    # 2. Existing active run with dummy asyncio task
    run = InvestigationRun(
        id="RUN-CANCEL-TEST",
        case_id="CASE-NMB-204",
        state="VALIDATING",
        created_at="2026-10-21T10:00:00Z",
        provider_mode="DEMO_FIXTURE",
        requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
        observations=[],
        sources=[],
        hypotheses=[],
        critiques=[],
        review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
        tool_events=[],
        disclaimer="Test",
    )
    orchestrator.runs[run.id] = run

    async def dummy():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            pass

    task = asyncio.create_task(dummy())
    orchestrator.tasks[run.id] = task

    success = orchestrator.cancel_investigation(run.id)
    assert success is True
    assert orchestrator.runs[run.id].state == "FAILED_TRUTHFULLY"
    try:
        await task
    except asyncio.CancelledError:
        pass



@pytest.mark.asyncio
async def test_subscribe_streaming_replay(orchestrator):
    case = CASES_STORE["CASE-NMB-204"]
    run_id = orchestrator.init_run(case)

    # Buffer a couple of test events
    orchestrator.event_buffers[run_id] = [
        {"seq": 1, "stage": "VALIDATE_SCHEMA", "type": "STAGE_START"},
        {"seq": 2, "stage": "VALIDATE_SCHEMA", "type": "STAGE_COMPLETE"},
        {"seq": 3, "stage": "HUMAN_REVIEW_READY", "type": "STAGE_COMPLETE"}
    ]
    orchestrator.runs[run_id].state = "HUMAN_REVIEW_READY"

    events_received = []
    async for ev in orchestrator.subscribe(run_id):
        events_received.append(ev)

    assert len(events_received) == 3
    assert events_received[0]["stage"] == "VALIDATE_SCHEMA"
    assert events_received[2]["stage"] == "HUMAN_REVIEW_READY"


@pytest.mark.asyncio
async def test_execute_run_zero_readings_fails_truthfully(orchestrator):
    base_case = CASES_STORE["CASE-NMB-204"]
    zero_case = ShipmentCase.model_validate(base_case.model_dump())
    zero_case.readings = []

    rid = orchestrator.start_investigation(zero_case)
    run = await orchestrator.wait_for_completion(rid)

    assert run.state == "FAILED_TRUTHFULLY"
    assert "0 sensor readings" in (run.failure_reason or "")


@pytest.mark.asyncio
async def test_execute_run_timeout_exception(orchestrator):
    case = CASES_STORE["CASE-NMB-204"]
    from unittest.mock import patch

    with patch.object(orchestrator.detector, "analyze_case", side_effect=TimeoutError("Wall-clock budget exceeded")):
        rid = orchestrator.start_investigation(case)
        run = await orchestrator.wait_for_completion(rid)

        assert run.state == "FAILED_TRUTHFULLY"
        assert "timeout limit" in (run.failure_reason or "")


@pytest.mark.asyncio
async def test_execute_run_unhandled_exception(orchestrator):
    case = CASES_STORE["CASE-NMB-204"]
    from unittest.mock import patch

    with patch.object(orchestrator.detector, "analyze_case", side_effect=RuntimeError("Corrupted time series")):
        rid = orchestrator.start_investigation(case)
        run = await orchestrator.wait_for_completion(rid)

        assert run.state == "FAILED_TRUTHFULLY"
        assert "Corrupted time series" in (run.failure_reason or "")


@pytest.mark.asyncio
async def test_execute_run_critique_validation_failure(orchestrator):
    case = CASES_STORE["CASE-NMB-204"]
    from unittest.mock import AsyncMock

    from apps.api.app.domain.models import SkepticCritique

    invalid_critique = SkepticCritique(
        hypothesis_id="HYP-NONEXISTENT-999",
        attack_summary="Invalid hypothesis reference.",
        unsupported_claims=[],
        ignored_contradictions=[],
        recommended_status="DOWNGRADED",
        rationale="Unknown hypothesis ID.",
    )
    orchestrator.nebius.run_skeptic_pass_async = AsyncMock(
        return_value=([invalid_critique], {"status": "DEMO_FIXTURE", "is_live": False})
    )

    rid = orchestrator.start_investigation(case)
    run = await orchestrator.wait_for_completion(rid)

    assert run.state == "FAILED_TRUTHFULLY"
    assert "Claims validator failed" in (run.failure_reason or "")


@pytest.mark.asyncio
async def test_execute_run_prohibited_claim_failure(orchestrator):
    case = CASES_STORE["CASE-NMB-204"]
    from unittest.mock import AsyncMock

    from apps.api.app.domain.models import Hypothesis

    prohibited_hyp = Hypothesis(
        id="HYP-01",
        label="REFRIGERATION_FAILURE",
        summary="This batch is compliant with FDA regulations and approved for immediate release.",
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=[],
        next_check="Check door seals.",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Does not establish core thermal equilibrium.",
    )
    orchestrator.nebius.generate_hypotheses_async = AsyncMock(
        return_value=([prohibited_hyp], {"status": "DEMO_FIXTURE", "is_live": False})
    )

    rid = orchestrator.start_investigation(case)
    run = await orchestrator.wait_for_completion(rid)

    assert run.state == "FAILED_TRUTHFULLY"
    assert "Claims validator failed" in (run.failure_reason or "")

