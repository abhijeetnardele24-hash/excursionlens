"""
apps/api/tests/test_async_concurrency.py — Concurrency, Bounded Execution, Timeout & SSE Race Elimination Tests
"""

import asyncio
import json
import os
from unittest.mock import patch

import pytest
from apps.api.app.agent.state_machine import InvestigationOrchestrator
from apps.api.app.domain.models import ShipmentCase


@pytest.fixture
def sample_case() -> ShipmentCase:
    fixture_path = os.path.join("packages", "fixtures", "nmb_204.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ShipmentCase.model_validate(data)


@pytest.mark.asyncio
async def test_mid_run_subscriber_receives_all_stages_without_duplicate_calls(sample_case):
    """Proves a mid-run subscriber receives all stages without race conditions or duplicate provider executions."""
    orchestrator = InvestigationOrchestrator()
    run_id = orchestrator.start_investigation(sample_case)

    # Let the investigation make partial progress
    await asyncio.sleep(0.08)

    # Subscribe mid-run
    events_received = []
    seq_numbers = []
    async for evt in orchestrator.subscribe(run_id):
        events_received.append(evt)
        seq = evt.get("seq", 0)
        seq_numbers.append(seq)
        if evt.get("stage") in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
            break

    # 1. Monotonically increasing sequence IDs without duplicates
    assert len(seq_numbers) > 0
    assert seq_numbers == sorted(seq_numbers)
    assert len(seq_numbers) == len(set(seq_numbers)), "Sequence numbers must be strictly unique"

    # 2. Both early stages (e.g. CREATED, VALIDATING) and terminal stages were received
    stages = [e.get("stage") for e in events_received]
    assert "CREATED" in stages
    assert "VALIDATING" in stages
    assert "NORMALIZING" in stages
    assert "EXCURSION_DETECTED" in stages
    assert "HUMAN_REVIEW_READY" in stages

    # 3. Only a single execution task was created
    assert len(orchestrator.tasks) == 1
    completed_run = orchestrator.get_run(run_id)
    assert completed_run is not None
    assert completed_run.state == "HUMAN_REVIEW_READY"


@pytest.mark.asyncio
async def test_multiple_concurrent_subscribers(sample_case):
    """Proves multiple concurrent subscribers receive complete streams without interference."""
    orchestrator = InvestigationOrchestrator()
    run_id = orchestrator.start_investigation(sample_case)

    async def collect_events():
        evts = []
        async for evt in orchestrator.subscribe(run_id):
            evts.append(evt)
            if evt.get("stage") in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
                break
        return evts

    # Spawn 3 concurrent listeners
    results = await asyncio.gather(
        collect_events(),
        collect_events(),
        collect_events()
    )

    for evts in results:
        stages = [e.get("stage") for e in evts]
        assert "CREATED" in stages
        assert "HUMAN_REVIEW_READY" in stages


@pytest.mark.asyncio
async def test_cancellation_transitions_state_truthfully(sample_case):
    """Proves that cancelling an in-flight investigation transitions truthfully to FAILED_TRUTHFULLY."""
    orchestrator = InvestigationOrchestrator()
    run_id = orchestrator.start_investigation(sample_case)

    # Cancel while task is running
    cancelled = orchestrator.cancel_investigation(run_id)
    assert cancelled is True

    # Await task until cancellation handler finishes
    task = orchestrator.tasks.get(run_id)
    if task:
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass

    res = orchestrator.get_run(run_id)
    assert res is not None
    assert res.state == "FAILED_TRUTHFULLY"
    assert "cancel" in (res.failure_reason or "").lower()


@pytest.mark.asyncio
async def test_investigation_timeout_enforcement(sample_case):
    """Proves that exceeding timeout triggers explicit timeout terminal state."""
    orchestrator = InvestigationOrchestrator()

    # Patch settings to have a 0.1 second timeout limit
    with patch("apps.api.app.config.settings.investigation_timeout_seconds", 0.1):
        # Force a sleep that exceeds timeout
        original_sleep = asyncio.sleep

        async def slow_sleep(sec):
            await original_sleep(0.25)

        with patch("asyncio.sleep", side_effect=slow_sleep):
            run_id = orchestrator.start_investigation(sample_case)

            # Collect until terminal
            async for evt in orchestrator.subscribe(run_id):
                if evt.get("stage") in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
                    break

            res = orchestrator.get_run(run_id)
            assert res is not None
            assert res.state == "FAILED_TRUTHFULLY"
            assert "timeout" in (res.failure_reason or "").lower()
