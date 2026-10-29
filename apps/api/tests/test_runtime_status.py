"""
apps/api/tests/test_runtime_status.py — Regression Tests for Runtime Provider & Mode Separation
"""

from unittest.mock import patch

from apps.api.app.main import app
from apps.api.app.providers.status import (
    evaluate_runtime_status,
    is_valid_credential,
)
from fastapi.testclient import TestClient


def test_is_valid_credential():
    assert not is_valid_credential(None)
    assert not is_valid_credential("")
    assert not is_valid_credential("   ")
    assert not is_valid_credential("your_nebius_api_key_here")
    assert not is_valid_credential("placeholder")
    assert not is_valid_credential("none")
    assert not is_valid_credential("<none>")
    assert is_valid_credential("valid-real-secret-key-12345")


def test_evaluate_runtime_status_missing_keys():
    status, mode, verified = evaluate_runtime_status(
        nebius_key=None,
        tavily_key=None,
        app_mode="live",
    )
    assert status == "NOT_CONFIGURED"
    assert mode == "DEMO_FIXTURE"
    assert verified is False


def test_evaluate_runtime_status_placeholder_keys():
    status, mode, verified = evaluate_runtime_status(
        nebius_key="your_nebius_token_factory_key_here",
        tavily_key="your_tavily_api_key_here",
        app_mode="live",
    )
    assert status == "NOT_CONFIGURED"
    assert mode == "DEMO_FIXTURE"
    assert verified is False


def test_evaluate_runtime_status_partial_nebius_only():
    status, mode, verified = evaluate_runtime_status(
        nebius_key="mock_key_nebius_valid_token_9999",
        tavily_key="",
        app_mode="live",
    )
    assert status == "PARTIAL_FAILURE"
    assert mode == "DEMO_FIXTURE_FALLBACK"
    assert verified is False


def test_evaluate_runtime_status_partial_tavily_only():
    status, mode, verified = evaluate_runtime_status(
        nebius_key="",
        tavily_key="mock_key_tavily_valid_search_8888",
        app_mode="live",
    )
    assert status == "PARTIAL_FAILURE"
    assert mode == "DEMO_FIXTURE_FALLBACK"
    assert verified is False


def test_evaluate_runtime_status_both_configured_pending_verification():
    status, mode, verified = evaluate_runtime_status(
        nebius_key="mock_key_nebius_valid_token_9999",
        tavily_key="mock_key_tavily_valid_search_8888",
        app_mode="live",
        verified_live_run=False,
        failed_live_attempt=False,
    )
    assert status == "CONFIGURED_PENDING_VERIFICATION"
    assert mode == "DEMO_FIXTURE"
    assert verified is False


def test_evaluate_runtime_status_both_configured_live_verified():
    status, mode, verified = evaluate_runtime_status(
        nebius_key="mock_key_nebius_valid_token_9999",
        tavily_key="mock_key_tavily_valid_search_8888",
        app_mode="live",
        verified_live_run=True,
        failed_live_attempt=False,
    )
    assert status == "LIVE_VERIFIED"
    assert mode == "LIVE_TOKEN_FACTORY"
    assert verified is True


def test_evaluate_runtime_status_failed_live_attempt():
    status, mode, verified = evaluate_runtime_status(
        nebius_key="mock_key_nebius_valid_token_9999",
        tavily_key="mock_key_tavily_valid_search_8888",
        app_mode="live",
        verified_live_run=False,
        failed_live_attempt=True,
    )
    assert status == "DEMO_FIXTURE_FALLBACK"
    assert mode == "DEMO_FIXTURE_FALLBACK"
    assert verified is False


def test_evaluate_runtime_status_explicit_fixture_mode():
    status, mode, verified = evaluate_runtime_status(
        nebius_key="mock_key_nebius_valid_token_9999",
        tavily_key="mock_key_tavily_valid_search_8888",
        app_mode="fixture",
        verified_live_run=True,
    )
    assert status == "DEMO_FIXTURE"
    assert mode == "DEMO_FIXTURE"
    assert verified is False



def test_api_health_endpoint_separation():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert "application_environment" in data
    assert "provider_status" in data
    assert "live_execution_verified" in data
    assert "provider_mode" in data

    # Verify that 'mode': 'live' is NOT returned
    assert data.get("mode") is None
    # When keys are absent in test environment, status must be NOT_CONFIGURED
    assert data["provider_status"] == "NOT_CONFIGURED"
    assert data["live_execution_verified"] is False
    assert data["provider_mode"] == "DEMO_FIXTURE"


def test_api_meta_endpoint_separation():
    client = TestClient(app)
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()

    assert "application_environment" in data
    assert "provider_status" in data
    assert "live_execution_verified" in data
    assert "provider_mode" in data
    assert data.get("mode") is None

    provider = data["provider"]
    assert provider["nebius_token_factory_configured"] is False
    assert provider["tavily_search_configured"] is False
    assert provider["status"] == "NOT_CONFIGURED"
    assert provider["live_verified"] is False


def test_api_health_with_simulated_live_run():
    client = TestClient(app)
    with patch(
        "apps.api.app.main.get_current_runtime_status",
        return_value=("LIVE_VERIFIED", "LIVE_TOKEN_FACTORY", True)
    ):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider_status"] == "LIVE_VERIFIED"
        assert data["provider_mode"] == "LIVE_TOKEN_FACTORY"
        assert data["live_execution_verified"] is True


def test_runtime_status_recency_live_then_fallback():
    from apps.api.app.config import settings
    from apps.api.app.domain.models import InvestigationRun
    from apps.api.app.main import get_current_runtime_status, orchestrator

    orchestrator.runs.clear()
    with patch.object(settings, "nebius_key", "mock_key_nebius_12345"), \
         patch.object(settings, "tavily_key", "mock_key_tavily_12345"):
        # Run 1: live verified
        run1 = InvestigationRun(
            id="RUN-LIVE-01",
            case_id="CASE-01",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-29T10:00:00Z",
            provider_mode="LIVE_TOKEN_FACTORY",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run1.id] = run1

        status, mode, verified = get_current_runtime_status()
        assert status == "LIVE_VERIFIED"
        assert mode == "LIVE_TOKEN_FACTORY"
        assert verified is True

        # Run 2: subsequent attempt falls back
        run2 = InvestigationRun(
            id="RUN-FALLBACK-02",
            case_id="CASE-01",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-29T10:05:00Z",
            provider_mode="DEMO_FIXTURE_FALLBACK",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run2.id] = run2

        status, mode, verified = get_current_runtime_status()
        assert status == "DEMO_FIXTURE_FALLBACK"
        assert mode == "DEMO_FIXTURE_FALLBACK"
        assert verified is False


def test_runtime_status_recency_live_then_failure():
    from apps.api.app.config import settings
    from apps.api.app.domain.models import InvestigationRun
    from apps.api.app.main import get_current_runtime_status, orchestrator

    orchestrator.runs.clear()
    with patch.object(settings, "nebius_key", "mock_key_nebius_12345"), \
         patch.object(settings, "tavily_key", "mock_key_tavily_12345"):
        run1 = InvestigationRun(
            id="RUN-LIVE-01",
            case_id="CASE-01",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-29T10:00:00Z",
            provider_mode="LIVE_TOKEN_FACTORY",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run1.id] = run1

        # Run 2: failed truthfully (claims validation error)
        run2 = InvestigationRun(
            id="RUN-FAIL-02",
            case_id="CASE-01",
            state="FAILED_TRUTHFULLY",
            failure_reason="Claims validator failed: Prohibited claim detected",
            created_at="2026-10-29T10:06:00Z",
            provider_mode="DEMO_FIXTURE_FALLBACK",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run2.id] = run2

        status, mode, verified = get_current_runtime_status()
        assert status == "DEMO_FIXTURE_FALLBACK"
        assert verified is False


def test_runtime_status_recency_live_then_timeout():
    from apps.api.app.config import settings
    from apps.api.app.domain.models import InvestigationRun
    from apps.api.app.main import get_current_runtime_status, orchestrator

    orchestrator.runs.clear()
    with patch.object(settings, "nebius_key", "mock_key_nebius_12345"), \
         patch.object(settings, "tavily_key", "mock_key_tavily_12345"):
        run1 = InvestigationRun(
            id="RUN-LIVE-01",
            case_id="CASE-01",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-29T10:00:00Z",
            provider_mode="LIVE_TOKEN_FACTORY",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run1.id] = run1

        # Run 2: timed out
        run2 = InvestigationRun(
            id="RUN-TIMEOUT-02",
            case_id="CASE-01",
            state="FAILED_TRUTHFULLY",
            failure_reason="Investigation exceeded configured timeout limit of 45.0s.",
            created_at="2026-10-29T10:07:00Z",
            provider_mode="DEMO_FIXTURE_FALLBACK",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run2.id] = run2

        status, mode, verified = get_current_runtime_status()
        assert status == "DEMO_FIXTURE_FALLBACK"
        assert verified is False


def test_runtime_status_recency_live_then_cancellation():
    from apps.api.app.config import settings
    from apps.api.app.domain.models import InvestigationRun
    from apps.api.app.main import get_current_runtime_status, orchestrator

    orchestrator.runs.clear()
    with patch.object(settings, "nebius_key", "mock_key_nebius_12345"), \
         patch.object(settings, "tavily_key", "mock_key_tavily_12345"):
        run1 = InvestigationRun(
            id="RUN-LIVE-01",
            case_id="CASE-01",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-29T10:00:00Z",
            provider_mode="LIVE_TOKEN_FACTORY",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run1.id] = run1

        # Run 2: cancelled
        run2 = InvestigationRun(
            id="RUN-CANCEL-02",
            case_id="CASE-01",
            state="FAILED_TRUTHFULLY",
            failure_reason="Investigation was cancelled by user.",
            created_at="2026-10-29T10:08:00Z",
            provider_mode="DEMO_FIXTURE_FALLBACK",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run2.id] = run2

        status, mode, verified = get_current_runtime_status()
        assert status == "DEMO_FIXTURE_FALLBACK"
        assert verified is False

        # Verify /api/health and /api/meta endpoints also reflect this recency
        client = TestClient(app)
        h_resp = client.get("/api/health")
        assert h_resp.status_code == 200
        assert h_resp.json()["provider_status"] == "DEMO_FIXTURE_FALLBACK"
        assert h_resp.json()["live_execution_verified"] is False

        m_resp = client.get("/api/meta")
        assert m_resp.status_code == 200
        assert m_resp.json()["provider_status"] == "DEMO_FIXTURE_FALLBACK"
        assert m_resp.json()["live_execution_verified"] is False


def test_runtime_status_recency_same_second_live_then_fallback():
    from apps.api.app.config import settings
    from apps.api.app.domain.models import InvestigationRun
    from apps.api.app.main import app, get_current_runtime_status, orchestrator

    orchestrator.runs.clear()
    with patch.object(settings, "nebius_key", "mock_key_nebius_12345"), \
         patch.object(settings, "tavily_key", "mock_key_tavily_12345"):
        # Run 1: live verified created at 10:00:00Z with high-sorting ID (e.g. RUN-ZZZ)
        run1 = InvestigationRun(
            id="RUN-ZZZ-LIVE-01",
            case_id="CASE-01",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-29T10:00:00Z",
            provider_mode="LIVE_TOKEN_FACTORY",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run1.id] = run1

        status, mode, verified = get_current_runtime_status()
        assert status == "LIVE_VERIFIED"
        assert verified is True

        # Run 2: created within the SAME SECOND (10:00:00Z) with low-sorting ID (e.g. RUN-AAA)
        run2 = InvestigationRun(
            id="RUN-AAA-FALLBACK-02",
            case_id="CASE-01",
            state="HUMAN_REVIEW_READY",
            created_at="2026-10-29T10:00:00Z",
            provider_mode="DEMO_FIXTURE_FALLBACK",
            requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
            observations=[],
            sources=[],
            hypotheses=[],
            critiques=[],
            review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
            tool_events=[],
        )
        orchestrator.runs[run2.id] = run2

        # Verify get_current_runtime_status reports the newer fallback
        status, mode, verified = get_current_runtime_status()
        assert status == "DEMO_FIXTURE_FALLBACK"
        assert mode == "DEMO_FIXTURE_FALLBACK"
        assert verified is False

        # Confirm /api/health and /api/meta both report the newer fallback
        client = TestClient(app)
        h_resp = client.get("/api/health")
        assert h_resp.status_code == 200
        h_data = h_resp.json()
        assert h_data["provider_status"] == "DEMO_FIXTURE_FALLBACK"
        assert h_data["provider_mode"] == "DEMO_FIXTURE_FALLBACK"
        assert h_data["live_execution_verified"] is False

        m_resp = client.get("/api/meta")
        assert m_resp.status_code == 200
        m_data = m_resp.json()
        assert m_data["provider_status"] == "DEMO_FIXTURE_FALLBACK"
        assert m_data["provider_mode"] == "DEMO_FIXTURE_FALLBACK"
        assert m_data["live_execution_verified"] is False
        assert m_data["provider"]["live_verified"] is False


