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
