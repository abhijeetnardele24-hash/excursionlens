"""
apps/api/tests/test_deploy_smoke.py — Unit Tests for Deployment Smoke Verifier
"""

from unittest.mock import MagicMock

import httpx
from scripts.deploy_smoke import verify_deployment


def test_deploy_smoke_empty_url():
    receipt, failures = verify_deployment("")
    assert receipt["status"] == "BLOCKED"
    assert "No deployment target URL provided" in failures[0]


def test_deploy_smoke_connection_error():
    receipt, failures = verify_deployment("http://invalid-nonexistent-domain-12345.local")
    assert receipt["status"] in ("CONNECTION_ERROR", "FAILED")
    assert len(failures) > 0


def test_deploy_smoke_mock_success(monkeypatch):
    mock_health = {"status": "ok", "commit": "test-sha-123", "provider_status": "NOT_CONFIGURED"}
    mock_meta = {"commit": "test-sha-123", "application_environment": "docker"}
    mock_case = {"shipment_id": "NMB-204"}

    def mock_get(self, url, *args, **kwargs):
        res = MagicMock(spec=httpx.Response)
        if url.endswith("/api/health"):
            res.status_code = 200
            res.json.return_value = mock_health
        elif url.endswith("/api/meta"):
            res.status_code = 200
            res.json.return_value = mock_meta
        elif url.endswith("/api/cases/NMB-204"):
            res.status_code = 200
            res.json.return_value = mock_case
        elif url.rstrip("/").endswith("example.com"):
            res.status_code = 200
            res.text = "<!DOCTYPE html><html><body>ExcursionLens</body></html>"
        else:
            res.status_code = 404
            res.text = "Not Found"
        return res

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    receipt, failures = verify_deployment("https://example.com", expected_sha="test-sha-123")
    assert receipt["status"] == "LIVE_DEPLOYED"
    assert receipt["commit_match"] is True
    assert len(failures) == 0


def test_deploy_smoke_mock_commit_mismatch(monkeypatch):
    mock_health = {"status": "ok", "commit": "wrong-sha", "provider_status": "NOT_CONFIGURED"}
    mock_meta = {"commit": "wrong-sha", "application_environment": "docker"}
    mock_case = {"shipment_id": "NMB-204"}

    def mock_get(self, url, *args, **kwargs):
        res = MagicMock(spec=httpx.Response)
        if url.endswith("/api/health"):
            res.status_code = 200
            res.json.return_value = mock_health
        elif url.endswith("/api/meta"):
            res.status_code = 200
            res.json.return_value = mock_meta
        elif url.endswith("/api/cases/NMB-204"):
            res.status_code = 200
            res.json.return_value = mock_case
        else:
            res.status_code = 200
            res.text = "<html><body>ExcursionLens</body></html>"
        return res

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    receipt, failures = verify_deployment("https://example.com", expected_sha="expected-sha-999")
    assert receipt["status"] == "FAILED"
    assert receipt["commit_match"] is False
    assert any("does not match expected" in f for f in failures)
