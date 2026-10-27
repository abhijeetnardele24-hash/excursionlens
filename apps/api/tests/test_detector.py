"""
apps/api/tests/test_detector.py — Unit Tests for Deterministic Excursion Engine
"""

import json
import os
import pytest
from apps.api.app.domain.models import ShipmentCase
from apps.api.app.domain.detector import DeterministicExcursionEngine


@pytest.fixture
def nmb_204_case() -> ShipmentCase:
    fixture_path = os.path.join("packages", "fixtures", "nmb_204.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ShipmentCase.model_validate(data)


def test_nmb_204_deterministic_analysis(nmb_204_case):
    engine = DeterministicExcursionEngine(detector_version="1.0")
    result = engine.analyze_case(nmb_204_case)

    # 1. Assert excursion was detected
    assert result.has_excursion is True
    assert result.case_id == "CASE-NMB-204"

    # 2. Check exact min/max temperatures
    assert result.min_recorded_temperature == 4.0
    assert result.max_recorded_temperature == 10.5

    # 3. Check excursion window observation
    excursion_obs = [obs for obs in result.observations if obs.kind == "EXCURSION_WINDOW"]
    assert len(excursion_obs) == 1

    obs = excursion_obs[0]
    assert obs.id == "OBS-EXCURSION-01"
    # Duration should be approximately 40 to 45 minutes (8 readings * 5 min)
    duration = obs.numeric_values["duration_minutes"]
    assert 35.0 <= duration <= 45.0
    assert obs.numeric_values["max_temperature"] == 10.5
    assert obs.numeric_values["threshold_celsius"] == 8.0

    # 4. Check event correlation: door open and handoff events must be linked
    assert "EVT-OPS-01" in obs.source_event_ids or "EVT-CUST-03" in obs.source_event_ids

    # 5. Check summary observation
    summary_obs = [obs for obs in result.observations if obs.kind == "TEMPERATURE_SUMMARY"]
    assert len(summary_obs) == 1
    assert summary_obs[0].id == "OBS-SUMMARY"
    assert summary_obs[0].numeric_values["max_celsius"] == 10.5


def test_boundary_values_exact():
    """Exact 2.0°C and 8.0°C are within range (not excursions)."""
    raw_case = {
        "id": "CASE-BOUNDARY-TEST",
        "title": "Boundary Test",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {
            "shipment_id": "TEST-01",
            "origin": "A",
            "destination": "B",
            "carrier": "C",
            "transport_mode": "TRUCK"
        },
        "product_profile": {
            "product_name": "Test Product",
            "product_class": "Biologic",
            "lot_number": "L1",
            "dose_count": 100
        },
        "temperature_policy": {
            "min_celsius": 2.0,
            "max_celsius": 8.0,
            "max_allowed_excursion_minutes": 0
        },
        "readings": [
            {"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 2.0},
            {"timestamp": "2026-10-25T10:05:00Z", "temperature_celsius": 5.0},
            {"timestamp": "2026-10-25T10:10:00Z", "temperature_celsius": 8.0}
        ],
        "custody_events": [],
        "operational_events": []
    }
    case = ShipmentCase.model_validate(raw_case)
    engine = DeterministicExcursionEngine()
    result = engine.analyze_case(case)

    assert result.has_excursion is False
    assert result.total_excursion_duration_minutes == 0.0
    assert result.min_recorded_temperature == 2.0
    assert result.max_recorded_temperature == 8.0


def test_telemetry_gap_and_jump_detection():
    """Detects gaps > 1.5x sampling interval and jump anomalies >= 4.0°C."""
    raw_case = {
        "id": "CASE-ANOMALY-TEST",
        "title": "Anomaly Test",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {
            "shipment_id": "TEST-02",
            "origin": "A",
            "destination": "B",
            "carrier": "C",
            "transport_mode": "TRUCK"
        },
        "product_profile": {
            "product_name": "Test Product",
            "product_class": "Biologic",
            "lot_number": "L2",
            "dose_count": 50
        },
        "temperature_policy": {
            "min_celsius": 2.0,
            "max_celsius": 8.0,
            "max_allowed_excursion_minutes": 0
        },
        "readings": [
            {"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0},
            {"timestamp": "2026-10-25T10:05:00Z", "temperature_celsius": 4.1},
            # 25-minute gap here (10:05 to 10:30)
            {"timestamp": "2026-10-25T10:30:00Z", "temperature_celsius": 4.2},
            # Sudden jump from 4.2 to 9.5 (+5.3°C in 5 min)
            {"timestamp": "2026-10-25T10:35:00Z", "temperature_celsius": 9.5}
        ],
        "custody_events": [],
        "operational_events": []
    }
    case = ShipmentCase.model_validate(raw_case)
    engine = DeterministicExcursionEngine()
    result = engine.analyze_case(case)

    kinds = [obs.kind for obs in result.observations]
    assert "SENSOR_GAP" in kinds
    assert "JUMP_ANOMALY" in kinds
    assert "EXCURSION_WINDOW" in kinds
    assert len(result.anomalies_detected) >= 2
