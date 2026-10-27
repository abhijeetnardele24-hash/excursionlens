"""
apps/api/tests/test_detector_multi_sensor.py — Tests for Multi-Sensor Telemetry Partitioning & Disagreement
"""

import pytest
from apps.api.app.domain.detector import DeterministicExcursionEngine
from apps.api.app.domain.models import (
    ProductProfile,
    SensorReading,
    ShipmentCase,
    ShipmentProfile,
    TemperaturePolicy,
)


@pytest.fixture
def multi_sensor_case() -> ShipmentCase:
    """
    Creates a multi-sensor shipment case with:
    - SENSOR-SURFACE: experiences rapid warming up to 12.0°C during transfer staging.
    - SENSOR-CORE: remains insulated, warming slowly to 6.8°C (within 2-8°C policy).
    - Significant surface vs core temperature differential (up to 5.2°C).
    """
    timestamps = [
        "2026-10-25T12:00:00Z",
        "2026-10-25T12:05:00Z",
        "2026-10-25T12:10:00Z",
        "2026-10-25T12:15:00Z",
        "2026-10-25T12:20:00Z",
        "2026-10-25T12:25:00Z",
        "2026-10-25T12:30:00Z",
        "2026-10-25T12:35:00Z",
    ]
    surface_temps = [4.5, 6.0, 9.5, 12.0, 11.5, 10.0, 7.5, 5.0]
    core_temps = [4.5, 4.8, 5.2, 6.8, 6.5, 6.0, 5.4, 4.9]

    readings = []
    # Interleave readings to verify proper pre-analysis sensor partitioning
    for ts, s_temp, c_temp in zip(timestamps, surface_temps, core_temps):
        readings.append(SensorReading(timestamp=ts, temperature_celsius=s_temp, sensor_id="SENSOR-SURFACE"))
        readings.append(SensorReading(timestamp=ts, temperature_celsius=c_temp, sensor_id="SENSOR-CORE"))

    return ShipmentCase(
        id="CASE-MULTI-SENSOR",
        title="Simultaneous Multi-Sensor Dual Probe Case",
        synthetic=True,
        created_at="2026-10-25T12:00:00Z",
        shipment=ShipmentProfile(
            shipment_id="SH-MULTI-01",
            origin="Hub X",
            destination="Depot Y",
            carrier="ColdLink",
        ),
        product_profile=ProductProfile(
            product_name="mRNA Lipid Biologic",
            product_class="Biologic",
            lot_number="LOT-MULTI",
            dose_count=5000,
        ),
        temperature_policy=TemperaturePolicy(
            min_celsius=2.0,
            max_celsius=8.0,
        ),
        readings=readings,
    )


def test_multi_sensor_partitioning_and_divergence(multi_sensor_case):
    engine = DeterministicExcursionEngine()
    result = engine.analyze_case(multi_sensor_case)

    # 1. Total readings analyzed equals total interleaved count
    assert result.reading_count == 16
    assert result.readings_analyzed == 16

    # 2. Excursion detected on surface probe only
    excursion_obs = [o for o in result.observations if o.kind == "EXCURSION_WINDOW"]
    assert len(excursion_obs) == 1
    s_obs = excursion_obs[0]
    assert s_obs.sensor_id == "SENSOR-SURFACE"
    assert s_obs.numeric_values["max_temperature"] == 12.0
    assert s_obs.numeric_values["auc_degree_minutes"] > 0
    assert s_obs.numeric_values["degree_minutes"] == s_obs.numeric_values["auc_degree_minutes"]

    # 3. Explicit surface vs core sensor disagreement detected
    disagreement_obs = [o for o in result.observations if o.kind == "SENSOR_DISAGREEMENT"]
    assert len(disagreement_obs) >= 1
    div = disagreement_obs[0]
    assert div.numeric_values["max_divergence_celsius"] >= 4.0
    assert "SENSOR-SURFACE" in div.source_event_ids
    assert "SENSOR-CORE" in div.source_event_ids
    assert "thermal inertia" in div.summary

    # 4. Global statistics
    assert result.max_recorded_temperature == 12.0
    assert result.min_recorded_temperature == 4.5
    assert result.has_excursion is True


def test_simultaneous_surface_and_core_excursions_do_not_double_count():
    """When both surface and core breach simultaneously, union aggregation must not double-count duration."""
    timestamps = [
        "2026-10-25T12:00:00Z",
        "2026-10-25T12:05:00Z",
        "2026-10-25T12:10:00Z",
        "2026-10-25T12:15:00Z",
        "2026-10-25T12:20:00Z",
    ]
    # Both surface and core are out of range for the same 4 readings (12:05 to 12:20)
    readings = []
    for ts in timestamps:
        readings.append(SensorReading(timestamp=ts, temperature_celsius=10.0, sensor_id="SENSOR-SURFACE"))
        readings.append(SensorReading(timestamp=ts, temperature_celsius=9.0, sensor_id="SENSOR-CORE"))

    case = ShipmentCase(
        id="CASE-DUAL-BREACH",
        title="Simultaneous Dual Sensor Breach",
        synthetic=True,
        created_at="2026-10-25T12:00:00Z",
        shipment=ShipmentProfile(
            shipment_id="SH-DUAL",
            origin="A",
            destination="B",
            carrier="C",
        ),
        product_profile=ProductProfile(
            product_name="Biologic Dual",
            product_class="Biologic",
            lot_number="LOT-DUAL",
            dose_count=100,
        ),
        temperature_policy=TemperaturePolicy(
            min_celsius=2.0,
            max_celsius=8.0,
        ),
        readings=readings,
    )
    engine = DeterministicExcursionEngine()
    result = engine.analyze_case(case)

    excursion_obs = [o for o in result.observations if o.kind == "EXCURSION_WINDOW"]
    # Two sensor-specific excursion observations (one for surface, one for core)
    assert len(excursion_obs) == 2
    assert {o.sensor_id for o in excursion_obs} == {"SENSOR-SURFACE", "SENSOR-CORE"}

    # Case-level total excursion duration is union, approximately 25 min (not 50 min!)
    assert 20.0 <= result.total_excursion_duration_minutes <= 30.0


def test_sensor_specific_gaps_not_confused_by_interleaved_sensors():
    """Gaps on one sensor must be identified without interference from concurrent sensors."""
    readings = [
        # Sensor A has a 30-minute gap between 12:05 and 12:35
        SensorReading(timestamp="2026-10-25T12:00:00Z", temperature_celsius=4.5, sensor_id="SENSOR-A"),
        SensorReading(timestamp="2026-10-25T12:05:00Z", temperature_celsius=4.5, sensor_id="SENSOR-A"),
        SensorReading(timestamp="2026-10-25T12:35:00Z", temperature_celsius=4.5, sensor_id="SENSOR-A"),
        # Sensor B samples steadily every 5 minutes throughout
        SensorReading(timestamp="2026-10-25T12:00:00Z", temperature_celsius=4.6, sensor_id="SENSOR-B"),
        SensorReading(timestamp="2026-10-25T12:10:00Z", temperature_celsius=4.6, sensor_id="SENSOR-B"),
        SensorReading(timestamp="2026-10-25T12:20:00Z", temperature_celsius=4.6, sensor_id="SENSOR-B"),
        SensorReading(timestamp="2026-10-25T12:30:00Z", temperature_celsius=4.6, sensor_id="SENSOR-B"),
    ]
    case = ShipmentCase(
        id="CASE-GAP-TEST",
        title="Sensor Gap Test",
        synthetic=True,
        created_at="2026-10-25T12:00:00Z",
        shipment=ShipmentProfile(
            shipment_id="SH-GAP",
            origin="A",
            destination="B",
            carrier="C",
        ),
        product_profile=ProductProfile(
            product_name="Biologic",
            product_class="Biologic",
            lot_number="LOT-G",
            dose_count=100,
        ),
        temperature_policy=TemperaturePolicy(
            min_celsius=2.0,
            max_celsius=8.0,
        ),
        readings=readings,
    )
    engine = DeterministicExcursionEngine()
    result = engine.analyze_case(case)

    gap_obs = [o for o in result.observations if o.kind == "SENSOR_GAP"]
    assert len(gap_obs) == 1
    assert gap_obs[0].sensor_id == "SENSOR-A"
    assert gap_obs[0].numeric_values["gap_duration_minutes"] == 30.0
