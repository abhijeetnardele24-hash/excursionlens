"""
apps/api/tests/test_api.py — Integration Tests for FastAPI Application Endpoints
"""

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
    assert 35.0 <= data["total_excursion_duration_minutes"] <= 45.0
    assert data["max_recorded_temperature"] == 10.5
    assert len(data["observations"]) >= 2


def test_full_investigation_workflow_and_reports():
    # 1. Start investigation
    res = client.post("/api/cases/CASE-NMB-204/investigations")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "started"
    run_id = data["run_id"]
    run = data["run"]

    assert run["state"] == "HUMAN_REVIEW_READY"
    assert run["review_posture"] == "QUARANTINE_PENDING_QUALIFIED_REVIEW"
    assert len(run["hypotheses"]) >= 2
    assert len(run["critiques"]) >= 1
    assert run["validation_result"]["passed"] is True

    # 2. Test Counterfactual endpoint
    cf_payload = {
        "intervention_type": "EXPEDITE_DOOR_CLOSING",
        "parameters": {"simulated_door_open_minutes": 5}
    }
    cf_res = client.post(f"/api/investigations/{run_id}/counterfactuals", json=cf_payload)
    assert cf_res.status_code == 200
    cf_data = cf_res.json()
    assert cf_data["simulated_excursion_duration_minutes"] == 0.0
    assert "prevents thermal breakthrough" in cf_data["result_summary"]

    # 3. Test HTML Report endpoint
    html_res = client.get(f"/api/investigations/{run_id}/report")
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers["content-type"]
    assert "ExcursionLens Investigation Report" in html_res.text
    assert "Mandatory Quality Boundary" in html_res.text
    assert "Qualified Human Disposition Sign-Off" in html_res.text

    # 4. Test JSON Report endpoint
    json_res = client.get(f"/api/investigations/{run_id}/report.json")
    assert json_res.status_code == 200
    report_data = json_res.json()
    assert report_data["id"] == run_id
    assert report_data["state"] == "HUMAN_REVIEW_READY"
    assert "disclaimer" in report_data
