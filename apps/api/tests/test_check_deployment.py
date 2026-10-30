"""
apps/api/tests/test_check_deployment.py — Unit Tests for Deployment Availability Verifier
"""

from unittest.mock import MagicMock

import httpx
from scripts.check_deployment import check_availability


def test_check_availability_mock_success(monkeypatch):
    mock_health = {
        "status": "ok",
        "commit": "test-sha-46d7c8a",
        "provider_mode": "DEMO_FIXTURE",
        "provider_status": "NOT_CONFIGURED",
        "live_execution_verified": False,
    }
    mock_meta = {"commit": "test-sha-46d7c8a"}

    def mock_get(self, url, *args, **kwargs):
        res = MagicMock(spec=httpx.Response)
        if url.endswith("/api/health"):
            res.status_code = 200
            res.json.return_value = mock_health
        elif url.endswith("/api/meta"):
            res.status_code = 200
            res.json.return_value = mock_meta
        elif url.endswith("/api/cases/CASE-NMB-204"):
            res.status_code = 200
            res.json.return_value = {"shipment_id": "NMB-204"}
        elif url.rstrip("/").endswith("example.com"):
            res.status_code = 200
            res.text = "<!DOCTYPE html><html><body>ExcursionLens</body></html>"
        else:
            res.status_code = 404
            res.text = "Not Found"
        return res

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    success, metrics, failures = check_availability(
        "https://example.com",
        expected_sha="test-sha-46d7c8a"
    )
    assert success is True
    assert metrics["commit_match"] is True
    assert metrics["deployed_sha"] == "test-sha-46d7c8a"
    assert len(failures) == 0


def test_check_availability_mock_sha_mismatch(monkeypatch):
    mock_health = {
        "status": "ok",
        "commit": "different-sha",
        "provider_mode": "DEMO_FIXTURE",
        "provider_status": "NOT_CONFIGURED",
        "live_execution_verified": False,
    }

    def mock_get(self, url, *args, **kwargs):
        res = MagicMock(spec=httpx.Response)
        if url.endswith("/api/health"):
            res.status_code = 200
            res.json.return_value = mock_health
        elif url.endswith("/api/meta") or url.endswith("/api/cases/CASE-NMB-204"):
            res.status_code = 200
            res.json.return_value = {}
        elif url.rstrip("/").endswith("example.com"):
            res.status_code = 200
            res.text = "<html><body>ExcursionLens</body></html>"
        return res

    monkeypatch.setattr(httpx.Client, "get", mock_get)

    success, metrics, failures = check_availability(
        "https://example.com",
        expected_sha="test-sha-46d7c8a"
    )
    assert success is False
    assert metrics["commit_match"] is False
    assert any("does not match expected" in f for f in failures)
