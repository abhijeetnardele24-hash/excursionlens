"""
apps/api/tests/test_orchestrator_deep_coverage.py — Tests for Orchestrator Cancellation, Pruning & Event Streaming
"""

import asyncio

import pytest
from apps.api.app.agent.state_machine import InvestigationOrchestrator
from apps.api.app.domain.models import InvestigationRun
from apps.api.app.main import CASES_STORE


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
