"""
apps/api/tests/test_detector_advanced.py — Unit Tests for Advanced Detector Hardening and Honest Counterfactuals
"""

import pydantic
import pytest
from apps.api.app.domain.counterfactual import CounterfactualEngine
from apps.api.app.domain.detector import DeterministicExcursionEngine
from apps.api.app.domain.models import CounterfactualRequest, SensorReading, ShipmentCase


@pytest.fixture
def minimal_case() -> ShipmentCase:
    return ShipmentCase.model_validate({
        "id": "CASE-TEST-ADV",
        "title": "Advanced Detector Test",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {
            "shipment_id": "TEST-ADV",
            "origin": "A",
            "destination": "B",
            "carrier": "C",
            "transport_mode": "TRUCK",
        },
        "product_profile": {
            "product_name": "Vaccine X",
            "product_class": "Biologic",
            "lot_number": "LOT-1",
            "dose_count": 100,
        },
        "temperature_policy": {
            "min_celsius": 2.0,
            "max_celsius": 8.0,
            "max_allowed_excursion_minutes": 0,
        },
        "readings": [
            {"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0, "sensor_id": "SENSOR-A"},
            {"timestamp": "2026-10-25T10:05:00Z", "temperature_celsius": 9.0, "sensor_id": "SENSOR-A"},
            {"timestamp": "2026-10-25T10:10:00Z", "temperature_celsius": 5.0, "sensor_id": "SENSOR-A"},
        ],
        "custody_events": [],
        "operational_events": [],
    })


def test_detector_rejects_timezone_naive_timestamps(minimal_case):
    engine = DeterministicExcursionEngine()
    # Inject timezone-naive timestamp string (no Z or offset)
    minimal_case.readings[0].timestamp = "2026-10-25T10:00:00"

    with pytest.raises(ValueError, match="is timezone-naive"):
        engine.analyze_case(minimal_case)


def test_detector_preserves_simultaneous_multi_sensor_readings(minimal_case):
    engine = DeterministicExcursionEngine()
    # Add simultaneous reading at same timestamp from a second sensor
    minimal_case.readings.append(
        SensorReading(
            timestamp="2026-10-25T10:00:00Z",
            temperature_celsius=4.5,
            sensor_id="SENSOR-B",
        )
    )
    result = engine.analyze_case(minimal_case)
    # Both readings should be preserved (4 total readings)
    summary = next(obs for obs in result.observations if obs.kind == "TEMPERATURE_SUMMARY")
    assert summary.numeric_values["reading_count"] == 4.0


def test_detector_rejects_excessive_readings(minimal_case):
    engine = DeterministicExcursionEngine()
    # Exceed MAX_READINGS_COUNT (10,000)
    minimal_case.readings = [
        SensorReading(
            timestamp=f"2026-10-25T10:00:{i % 60:02d}Z",
            temperature_celsius=5.0,
            sensor_id="S1",
        )
        for i in range(10_001)
    ]
    with pytest.raises(ValueError, match="exceeds maximum reading limit"):
        engine.analyze_case(minimal_case)


def test_counterfactual_rejects_unknown_intervention():
    # Strict Literal validation rejects unknown intervention enum
    with pytest.raises((ValueError, pydantic.ValidationError)):
        CounterfactualRequest(
            intervention_type="MAGIC_TELEPORTATION",  # type: ignore
            parameters={},
        )


def test_counterfactual_produces_honest_calculated_narrative(minimal_case):
    cf_engine = CounterfactualEngine()
    req = CounterfactualRequest(
        intervention_type="EXPEDITE_DOOR_CLOSING",
        parameters={"simulated_door_open_minutes": 5},
    )
    res = cf_engine.simulate(minimal_case, req, "RUN-TEST")
    assert res.intervention_type == "EXPEDITE_DOOR_CLOSING"
    assert "Synthetic sensitivity replay" in res.result_summary
    assert "Sensitivity replay assumption" in res.limits
