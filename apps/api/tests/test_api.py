"""
apps/api/tests/test_api.py — Integration Tests for FastAPI Application Endpoints
"""

import time

import pytest
from apps.api.app.main import app, load_default_fixtures
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_fixtures():
    load_default_fixtures()


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_meta_endpoint():
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    assert "safety_disclaimer" in data
    assert "provider" in data
    assert "selected_deep_model" in data["provider"]


def test_sample_case_endpoint():
    res = client.get("/api/cases/sample")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "CASE-NMB-204"
    assert data["shipment"]["shipment_id"] == "NMB-204"
    assert len(data["readings"]) > 20


def test_deterministic_analyze_endpoint():
    res = client.post("/api/cases/CASE-NMB-204/analyze")
    assert res.status_code == 200
    data = res.json()
    assert data["has_excursion"] is True
    assert data["total_excursion_duration_minutes"] == 40.0
    assert data["max_recorded_temperature"] == 10.5
    assert len(data["observations"]) >= 2


def test_single_execution_workflow_and_sse():
    # 1. Start investigation returns immediately
    res = client.post("/api/cases/CASE-NMB-204/investigations")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "started"
    run_id = data["run_id"]
    assert run_id.startswith("RUN-")

    # 2. Wait for background execution to reach terminal state
    deadline = time.time() + 10.0
    run_data = None
    while time.time() < deadline:
        get_res = client.get(f"/api/investigations/{run_id}")
        assert get_res.status_code == 200
        run_data = get_res.json()
        if run_data["state"] in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY"):
            break
        time.sleep(0.1)

    assert run_data is not None
    assert run_data["state"] == "HUMAN_REVIEW_READY"
    assert run_data["review_posture"] == "QUARANTINE_PENDING_QUALIFIED_REVIEW"
    assert len(run_data["hypotheses"]) >= 2
    assert len(run_data["critiques"]) >= 1
    assert run_data["validation_result"]["passed"] is True

    # 3. Connect to SSE stream: should replay past events idempotently
    sse_res = client.get(f"/api/investigations/{run_id}/events")
    assert sse_res.status_code == 200
    assert "text/event-stream" in sse_res.headers["content-type"]
    assert "stage_update" in sse_res.text

    # 4. Unknown run ID fails with 404
    bad_res = client.get("/api/investigations/RUN-NONEXISTENT/events")
    assert bad_res.status_code == 404

    # 5. Counterfactual sensitivity replay
    cf_payload = {
        "intervention_type": "EXPEDITE_DOOR_CLOSING",
        "parameters": {"max_door_open_minutes": 5.0}
    }
    cf_res = client.post(f"/api/investigations/{run_id}/counterfactuals", json=cf_payload)
    assert cf_res.status_code == 200
    cf_data = cf_res.json()
    assert cf_data["simulated_excursion_duration_minutes"] == 0.0
    assert "Synthetic sensitivity replay" in cf_data["result_summary"]

    # 6. HTML Report endpoint with escaping
    html_res = client.get(f"/api/investigations/{run_id}/report")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert "ExcursionLens Investigation Report" in html_res.text
    assert "Decision-Support Boundary:" in html_res.text
    assert "Qualified Human Disposition Sign-Off" in html_res.text

    # 7. JSON Report endpoint
    json_res = client.get(f"/api/investigations/{run_id}/report.json")
    assert json_res.status_code == 200
    report_data = json_res.json()
    assert report_data["id"] == run_id
    assert report_data["state"] == "HUMAN_REVIEW_READY"


def test_security_headers_and_payload_limits():
    res = client.get("/api/health")
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in res.headers["content-security-policy"]

    # 1. Non-integer Content-Length header returns 400
    res_non_int = client.post(
        "/api/cases/validate",
        content="{}",
        headers={"content-type": "application/json", "content-length": "invalid-non-int"},
    )
    assert res_non_int.status_code == 400
    assert "Invalid Content-Length header." in res_non_int.text

    # 2. Negative Content-Length header returns 400
    res_neg = client.post(
        "/api/cases/validate",
        content="{}",
        headers={"content-type": "application/json", "content-length": "-42"},
    )
    assert res_neg.status_code == 400
    assert "Malformed Content-Length header." in res_neg.text

    # 3. Payload above configured maximum returns 413
    oversized = "a" * (2 * 1024 * 1024 + 100)
    big_res = client.post(
        "/api/cases/validate",
        content=oversized,
        headers={"content-type": "application/json", "content-length": str(len(oversized))},
    )
    assert big_res.status_code == 413
    assert "Request payload exceeds maximum allowed size." in big_res.text

    # 4. Valid payload at or below limit proceeds safely
    valid_res = client.post(
        "/api/cases/validate",
        content="{}",
        headers={"content-type": "application/json", "content-length": "2"},
    )
    assert valid_res.status_code in (200, 422)  # Either accepted or schema validation error, not 400/413/500
