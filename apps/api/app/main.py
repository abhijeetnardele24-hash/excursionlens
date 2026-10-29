"""
apps/api/app/main.py — ExcursionLens Production FastAPI Application

Serves:
- REST API for Case Ingestion, Deterministic Excursion Analysis, and Agent Orchestration
- Server-Sent Events (SSE) for Real-Time Stage Transition Streaming (Single-Execution Architecture)
- Static Frontend SPA serving for production single-container deployment
- Health and Metadata endpoints (/api/health, /api/meta)
- Hardened with rate limiting, payload bounds, security headers, and safe CORS
"""

import asyncio
import json
import os
import subprocess
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .agent.state_machine import InvestigationOrchestrator
from .config import settings
from .domain.counterfactual import CounterfactualEngine
from .domain.detector import DeterministicExcursionEngine
from .domain.models import (
    CaseAnalysisResult,
    CounterfactualRequest,
    ShipmentCase,
)
from .domain.validator import DeterministicClaimsValidator
from .providers.status import ProviderStatus, evaluate_runtime_status, is_valid_credential
from .reports.generator import generate_printable_html_report

# In-memory case repository
CASES_STORE: dict[str, ShipmentCase] = {}

# In-memory sliding-window rate limiter
RATE_LIMIT_RECORDS: dict[str, list[float]] = defaultdict(list)


def get_git_commit_sha() -> str:
    env_sha = os.environ.get("APP_COMMIT_SHA") or os.environ.get("GIT_COMMIT") or os.environ.get("GITHUB_SHA")
    if env_sha and env_sha.strip() and env_sha.strip() != "unknown":
        return env_sha.strip()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def load_default_fixtures():
    nmb_path = os.path.join("packages", "fixtures", "nmb_204.json")
    if os.path.exists(nmb_path):
        with open(nmb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            case = ShipmentCase.model_validate(data)
            CASES_STORE[case.id] = case


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_default_fixtures()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evidence-first Cold-Chain Temperature Excursion Investigation Decision-Support System",
    lifespan=lifespan,
)

# CORS Allowlist
allow_all = "*" in settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else settings.cors_origins,
    allow_credentials=not allow_all,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # 1. Payload size check
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_request_size_bytes:
        return Response(content="Request payload exceeds maximum allowed size.", status_code=413)

    # 2. Sliding window rate limiting (applied only to API endpoints)
    if request.url.path.startswith("/api") and not request.url.path.endswith("/events"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - 60.0

        # Clean old requests
        timestamps = [t for t in RATE_LIMIT_RECORDS[client_ip] if t > cutoff]
        timestamps.append(now)
        RATE_LIMIT_RECORDS[client_ip] = timestamps

        if len(timestamps) > settings.rate_limit_per_minute:
            return Response(content="Rate limit exceeded. Please wait before retrying.", status_code=429)

    response = await call_next(request)

    # 3. Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; font-src 'self' data:; "
        "img-src 'self' data:; connect-src 'self' ws: wss:;"
    )
    return response


orchestrator = InvestigationOrchestrator()
counterfactual_engine = CounterfactualEngine()
detector = DeterministicExcursionEngine()
validator = DeterministicClaimsValidator()


# ==============================================================================
# Health and Metadata Endpoints
# ==============================================================================

def get_current_runtime_status() -> tuple[ProviderStatus, str, bool]:
    verified_live = False
    failed_live = False
    for r in orchestrator.runs.values():
        if r.provider_mode == "LIVE_TOKEN_FACTORY":
            verified_live = True
        elif r.provider_mode in ("DEMO_FIXTURE_FALLBACK", "FAILED"):
            failed_live = True

    return evaluate_runtime_status(
        nebius_key=settings.nebius_key,
        tavily_key=settings.tavily_key,
        app_mode=settings.app_mode,
        verified_live_run=verified_live,
        failed_live_attempt=failed_live,
    )


@app.get("/api/health")
def health():
    p_status, p_mode, live_verified = get_current_runtime_status()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "application_environment": settings.application_environment,
        "provider_status": p_status,
        "live_execution_verified": live_verified,
        "provider_mode": p_mode,
    }


@app.get("/api/meta")
def meta():
    p_status, p_mode, live_verified = get_current_runtime_status()
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "commit": get_git_commit_sha(),
        "application_environment": settings.application_environment,
        "provider_status": p_status,
        "live_execution_verified": live_verified,
        "provider_mode": p_mode,
        "provider": {
            "nebius_token_factory_configured": is_valid_credential(settings.nebius_key),
            "tavily_search_configured": is_valid_credential(settings.tavily_key),
            "selected_fast_model": settings.nvidia_fast_model_id,
            "selected_deep_model": settings.nvidia_deep_model_id,
            "status": p_status,
            "live_verified": live_verified,
        },
        "safety_disclaimer": (
            "Investigation-support output generated from synthetic or user-supplied evidence. "
            "It does not determine product safety, potency, regulatory compliance or disposition. "
            "Follow organizational SOPs and obtain review from an authorized quality professional."
        ),
    }


# ==============================================================================
# Case Endpoints
# ==============================================================================

@app.get("/api/cases/sample")
def get_sample_case():
    if "CASE-NMB-204" in CASES_STORE:
        return CASES_STORE["CASE-NMB-204"]
    raise HTTPException(status_code=404, detail="Sample case NMB-204 not found.")


@app.post("/api/cases/validate")
def validate_case(payload: dict[str, Any]):
    try:
        case = ShipmentCase.model_validate(payload)
        return {
            "valid": True,
            "case_id": case.id,
            "readings_count": len(case.readings),
            "custody_events_count": len(case.custody_events),
            "operational_events_count": len(case.operational_events),
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)],
        }


@app.post("/api/cases")
def create_case(case: ShipmentCase):
    CASES_STORE[case.id] = case
    return {"status": "created", "case_id": case.id}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    if case_id in CASES_STORE:
        return CASES_STORE[case_id]
    raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")


@app.post("/api/cases/{case_id}/analyze")
def analyze_case_deterministic(case_id: str) -> CaseAnalysisResult:
    if case_id not in CASES_STORE:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    case = CASES_STORE[case_id]
    return detector.analyze_case(case)


# ==============================================================================
# Single-Execution Investigation Endpoints & Real-Time SSE
# ==============================================================================

@app.post("/api/cases/{case_id}/investigations")
async def start_investigation(case_id: str, background_tasks: BackgroundTasks):
    """
    Creates exactly ONE investigation run bound to the specified case.
    Returns run_id immediately and executes in the background.
    """
    if case_id not in CASES_STORE:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    case = CASES_STORE[case_id]

    run_id = orchestrator.init_run(case)
    background_tasks.add_task(orchestrator.execute_run_background, run_id, case)
    return {
        "status": "started",
        "run_id": run_id,
        "case_id": case.id,
    }


@app.get("/api/investigations/{run_id}/events")
async def stream_investigation_events(run_id: str):
    """
    Server-Sent Events (SSE) that observes the existing background run.
    Replays buffered past events and streams live transitions without starting a second execution.
    """
    if run_id not in orchestrator.runs:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")

    async def event_generator():
        try:
            async for event in orchestrator.subscribe(run_id):
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/investigations/{run_id}")
def get_investigation(run_id: str):
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")
    return run


@app.post("/api/investigations/{run_id}/cancel")
def cancel_investigation(run_id: str):
    success = orchestrator.cancel_investigation(run_id)
    return {"status": "cancelled" if success else "not_running", "run_id": run_id}


@app.delete("/api/investigations/{run_id}")
def delete_investigation(run_id: str):
    orchestrator.cancel_investigation(run_id)
    orchestrator.runs.pop(run_id, None)
    orchestrator.cases.pop(run_id, None)
    orchestrator.event_buffers.pop(run_id, None)
    orchestrator.listeners.pop(run_id, None)
    orchestrator.tasks.pop(run_id, None)
    return {"status": "deleted", "run_id": run_id}


@app.post("/api/investigations/{run_id}/counterfactuals")
def run_counterfactual(run_id: str, request: CounterfactualRequest):
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")
    case = orchestrator.cases.get(run_id) or CASES_STORE.get(run.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{run.case_id}' not found.")

    res = counterfactual_engine.simulate(case, request, run_id)
    is_valid, errors = validator.validate_counterfactual(res)
    if not is_valid:
        raise HTTPException(
            status_code=500,
            detail=f"Counterfactual validation failed closed: {'; '.join(errors)}"
        )
    run.counterfactual = res
    return res


@app.get("/api/investigations/{run_id}/report")
def get_html_report(run_id: str):
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")
    case = orchestrator.cases.get(run_id) or CASES_STORE.get(run.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{run.case_id}' not found.")

    html = generate_printable_html_report(run, case)
    html_errors = validator.validate_text(html, "HTML Report")
    if html_errors:
        raise HTTPException(
            status_code=500,
            detail=f"HTML report failed deterministic safety checks: {'; '.join(html_errors)}"
        )
    return HTMLResponse(content=html)


@app.get("/api/investigations/{run_id}/report.json")
def get_json_report(run_id: str):
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")
    is_valid, errors = validator.inspect_complete_run(run.model_dump())
    if not is_valid:
        raise HTTPException(
            status_code=500,
            detail=f"JSON report failed deterministic safety checks: {'; '.join(errors)}"
        )
    return run


# Mount frontend static distribution if built
web_dist = os.path.join("apps", "web", "dist")
if os.path.exists(web_dist):
    app.mount("/", StaticFiles(directory=web_dist, html=True), name="static")
