"""
apps/api/tests/test_api_endpoints_coverage.py — Deep Coverage Tests for FastAPI Endpoints in main.py
"""

from apps.api.app.domain.models import InvestigationRun
from apps.api.app.main import CASES_STORE, app, orchestrator
from fastapi.testclient import TestClient


def test_cases_validate_valid_and_invalid():
    client = TestClient(app)
    # 1. Valid case
    valid_payload = CASES_STORE["CASE-NMB-204"].model_dump()
    res = client.post("/api/cases/validate", json=valid_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["case_id"] == "CASE-NMB-204"

    # 2. Invalid payload
    invalid_payload = {"id": "BAD-CASE", "readings": "not-a-list"}
    res2 = client.post("/api/cases/validate", json=invalid_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["valid"] is False
    assert len(data2["errors"]) > 0


def test_cases_crud_and_not_found():
    client = TestClient(app)

    # 1. Create a custom case
    base_case = CASES_STORE["CASE-NMB-204"].model_dump()
    base_case["id"] = "CASE-CUSTOM-TEST-01"
    create_res = client.post("/api/cases", json=base_case)
    assert create_res.status_code == 200
    assert create_res.json()["status"] == "created"

    # 2. Retrieve the created case
    get_res = client.get("/api/cases/CASE-CUSTOM-TEST-01")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == "CASE-CUSTOM-TEST-01"

    # 3. Retrieve non-existent case -> 404
    missing_res = client.get("/api/cases/NON-EXISTENT-CASE-999")
    assert missing_res.status_code == 404

    # 4. Analyze non-existent case -> 404
    analyze_missing = client.post("/api/cases/NON-EXISTENT-CASE-999/analyze")
    assert analyze_missing.status_code == 404


def test_investigation_not_found_routes():
    client = TestClient(app)

    # Missing case in investigation start -> 404
    start_missing = client.post("/api/cases/DOES-NOT-EXIST-CASE/investigations")
    assert start_missing.status_code == 404

    # Non-existent run endpoints -> 404
    assert client.get("/api/investigations/NON-EXISTENT-RUN").status_code == 404
    assert client.get("/api/investigations/NON-EXISTENT-RUN/events").status_code == 404
    assert client.post("/api/investigations/NON-EXISTENT-RUN/counterfactuals", json={
        "intervention_type": "EXPEDITE_DOOR_CLOSING",
        "parameters": {}
    }).status_code == 404
    assert client.get("/api/investigations/NON-EXISTENT-RUN/report").status_code == 404
    assert client.get("/api/investigations/NON-EXISTENT-RUN/packet").status_code == 404


def test_investigation_incomplete_report_and_packet():
    client = TestClient(app)

    # Register a run with prohibited release claim to trigger safety failure
    safety_fail_run = InvestigationRun(
        id="RUN-INCOMPLETE-TEST",
        case_id="CASE-NMB-204",
        state="VALIDATING",
        created_at="2026-10-21T10:00:00Z",
        provider_mode="DEMO_FIXTURE",
        requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
        observations=[],
        sources=[],
        hypotheses=[
            {
                "id": "HYP-BAD",
                "label": "Bad",
                "summary": "The product is safe for immediate release.",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": [],
                "unknowns": ["Unknown"],
                "next_check": "None",
                "confidence_band": "HIGH",
                "status": "LEADING",
                "what_it_does_not_establish": "Nothing"
            }
        ],
        critiques=[],
        review_posture="QUARANTINE_PENDING_QUALIFIED_REVIEW",
        tool_events=[],
        disclaimer="Test",
    )
    orchestrator.runs["RUN-INCOMPLETE-TEST"] = safety_fail_run
    orchestrator.cases["RUN-INCOMPLETE-TEST"] = CASES_STORE["CASE-NMB-204"]

    # Prohibited claim -> 500 on report.json
    json_res = client.get("/api/investigations/RUN-INCOMPLETE-TEST/report.json")
    assert json_res.status_code == 500
    assert "safety checks" in json_res.json()["detail"].lower()


def test_investigation_cancel_and_delete_routes():
    client = TestClient(app)

    cancel_run = InvestigationRun(
        id="RUN-CANCEL-ROUTE-TEST",
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
    orchestrator.runs["RUN-CANCEL-ROUTE-TEST"] = cancel_run

    # When not actively in task map, cancel returns not_running
    cancel_res = client.post("/api/investigations/RUN-CANCEL-ROUTE-TEST/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "not_running"

    # Delete route removes run
    del_res = client.delete("/api/investigations/RUN-CANCEL-ROUTE-TEST")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
    assert "RUN-CANCEL-ROUTE-TEST" not in orchestrator.runs


def test_counterfactual_simulate_route():
    client = TestClient(app)

    # First start an investigation or register a completed run
    completed_run = InvestigationRun(
        id="RUN-CF-TEST",
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
    orchestrator.runs["RUN-CF-TEST"] = completed_run
    orchestrator.cases["RUN-CF-TEST"] = CASES_STORE["CASE-NMB-204"]

    cf_success = client.post("/api/investigations/RUN-CF-TEST/counterfactuals", json={
        "intervention_type": "EXPEDITE_DOOR_CLOSING",
        "parameters": {"max_door_open_minutes": 5.0}
    })
    assert cf_success.status_code == 200
    data = cf_success.json()
    assert data["intervention_type"] == "EXPEDITE_DOOR_CLOSING"
    assert data["original_excursion_duration_minutes"] == 40.0
    assert data["simulated_excursion_duration_minutes"] == 0.0
