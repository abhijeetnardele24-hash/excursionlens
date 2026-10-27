"""
apps/api/app/main.py — ExcursionLens Production FastAPI Application

Serves:
- REST API for Case Ingestion, Deterministic Excursion Analysis, and Agent Orchestration
- Server-Sent Events (SSE) for Real-Time Stage Transition Streaming
- Static Frontend SPA serving for production single-container deployment
- Health and Metadata endpoints (/api/health, /api/meta)
"""

import asyncio
import json
import os
import subprocess
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
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
    InvestigationRun,
    ShipmentCase,
)
from .reports.generator import generate_printable_html_report

# In-memory case and run repository
CASES_STORE: dict[str, ShipmentCase] = {}
RUNS_STORE: dict[str, InvestigationRun] = {}

def get_git_commit_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
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
            print(f"📦 Loaded default fixture case: {case.id} ({case.shipment.shipment_id})")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_default_fixtures()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evidence-first Cold-Chain Temperature Excursion Investigation Agent",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = InvestigationOrchestrator()
counterfactual_engine = CounterfactualEngine()
detector = DeterministicExcursionEngine()


# ==============================================================================
# Health and Metadata Endpoints
# ==============================================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "mode": settings.app_mode
    }


@app.get("/api/meta")
def meta():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "commit": get_git_commit_sha(),
        "mode": settings.app_mode,
        "provider": {
            "nebius_token_factory_configured": bool(settings.nebius_key and not settings.nebius_key.startswith("your_")),
            "tavily_search_configured": bool(settings.tavily_key and not settings.tavily_key.startswith("your_")),
            "selected_fast_model": settings.nvidia_fast_model_id,
            "selected_deep_model": settings.nvidia_deep_model_id,
        },
        "safety_disclaimer": (
            "Investigation support only. Not a product disposition, medical decision, "
            "legal conclusion, or regulatory determination."
        )
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
            "operational_events_count": len(case.operational_events)
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)]
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
# Investigation Endpoints & Real-Time SSE
# ==============================================================================

@app.post("/api/cases/{case_id}/investigations")
async def start_investigation(case_id: str):
    if case_id not in CASES_STORE:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
    case = CASES_STORE[case_id]

    import uuid
    run_id = f"RUN-{uuid.uuid4().hex[:8]}"

    # Execute all stages and store the final run
    final_run: InvestigationRun | None = None
    async for event in orchestrator.run_investigation(case, run_id=run_id):
        if "completed_run" in event.get("data", {}):
            final_run = InvestigationRun.model_validate(event["data"]["completed_run"])
        elif "run" in event:
            final_run = InvestigationRun.model_validate(event["run"])

    if final_run:
        RUNS_STORE[run_id] = final_run

    return {"status": "started", "run_id": run_id, "run": final_run}


@app.get("/api/investigations/{run_id}/events")
async def stream_investigation_events(run_id: str):
    """Server-Sent Events (SSE) streaming live investigation progress."""
    # Find matching case
    case = CASES_STORE.get("CASE-NMB-204")
    if not case:
        raise HTTPException(status_code=404, detail="Case not available for streaming.")

    async def event_generator():
        async for event in orchestrator.run_investigation(case, run_id=run_id):
            if "completed_run" in event.get("data", {}):
                RUNS_STORE[run_id] = InvestigationRun.model_validate(event["data"]["completed_run"])
            elif "run" in event:
                RUNS_STORE[run_id] = InvestigationRun.model_validate(event["run"])
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.3)  # brief pause for visual comprehension

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/investigations/{run_id}")
def get_investigation(run_id: str):
    if run_id in RUNS_STORE:
        return RUNS_STORE[run_id]
    raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")


@app.post("/api/investigations/{run_id}/counterfactuals")
def run_counterfactual(run_id: str, request: CounterfactualRequest):
    if run_id not in RUNS_STORE:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")
    run = RUNS_STORE[run_id]
    case = CASES_STORE.get(run.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{run.case_id}' not found.")

    res = counterfactual_engine.simulate(case, request, run_id)
    run.counterfactual = res
    return res


@app.get("/api/investigations/{run_id}/report")
def get_html_report(run_id: str):
    if run_id not in RUNS_STORE:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")
    run = RUNS_STORE[run_id]
    case = CASES_STORE.get(run.case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{run.case_id}' not found.")

    html = generate_printable_html_report(run, case)
    return HTMLResponse(content=html)


@app.get("/api/investigations/{run_id}/report.json")
def get_json_report(run_id: str):
    if run_id not in RUNS_STORE:
        raise HTTPException(status_code=404, detail=f"Investigation run '{run_id}' not found.")
    return RUNS_STORE[run_id]


# Mount frontend static distribution if built
web_dist = os.path.join("apps", "web", "dist")
if os.path.exists(web_dist):
    app.mount("/", StaticFiles(directory=web_dist, html=True), name="static")
