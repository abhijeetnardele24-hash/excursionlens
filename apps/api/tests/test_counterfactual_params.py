"""
apps/api/tests/test_counterfactual_params.py — Contract Tests for Counterfactual Parameters
"""

import pytest
from apps.api.app.domain.counterfactual import CounterfactualEngine
from apps.api.app.domain.models import (
    CounterfactualParameters,
    CounterfactualRequest,
    ProductProfile,
    SensorReading,
    ShipmentCase,
    ShipmentProfile,
    TemperaturePolicy,
)
from pydantic import ValidationError


@pytest.fixture
def test_case() -> ShipmentCase:
    readings = [
        SensorReading(timestamp="2026-10-25T10:00:00Z", temperature_celsius=4.5, sensor_id="S-01"),
        SensorReading(timestamp="2026-10-25T10:05:00Z", temperature_celsius=5.0, sensor_id="S-01"),
        SensorReading(timestamp="2026-10-25T10:10:00Z", temperature_celsius=10.0, sensor_id="S-01"),
        SensorReading(timestamp="2026-10-25T10:15:00Z", temperature_celsius=12.0, sensor_id="S-01"),
        SensorReading(timestamp="2026-10-25T10:20:00Z", temperature_celsius=11.5, sensor_id="S-01"),
        SensorReading(timestamp="2026-10-25T10:25:00Z", temperature_celsius=10.5, sensor_id="S-01"),
        SensorReading(timestamp="2026-10-25T10:30:00Z", temperature_celsius=9.0, sensor_id="S-01"),
        SensorReading(timestamp="2026-10-25T10:35:00Z", temperature_celsius=5.0, sensor_id="S-01"),
    ]
    return ShipmentCase(
        id="CASE-CF-TEST",
        title="Counterfactual Parameter Contract Test",
        synthetic=True,
        created_at="2026-10-25T10:00:00Z",
        shipment=ShipmentProfile(
            shipment_id="SH-001",
            origin="Depot A",
            destination="Clinic B",
            carrier="ColdFleet",
        ),
        product_profile=ProductProfile(
            product_name="Biologic Beta",
            product_class="Vaccine",
            lot_number="LOT-99",
            dose_count=1000,
        ),
        temperature_policy=TemperaturePolicy(
            min_celsius=2.0,
            max_celsius=8.0,
        ),
        readings=readings,
    )


def test_reject_nan_and_infinity_in_parameters():
    with pytest.raises(ValidationError):
        CounterfactualParameters(max_door_open_minutes=float("nan"))

    with pytest.raises(ValidationError):
        CounterfactualParameters(max_door_open_minutes=float("inf"))

    with pytest.raises(ValidationError):
        CounterfactualParameters(core_lag_factor=float("nan"))

    with pytest.raises(ValidationError):
        CounterfactualParameters(core_lag_factor=float("-inf"))


def test_reject_out_of_bounds_parameters():
    # Door minutes must be > 0 and <= 120
    with pytest.raises(ValidationError):
        CounterfactualParameters(max_door_open_minutes=0.0)

    with pytest.raises(ValidationError):
        CounterfactualParameters(max_door_open_minutes=-5.0)

    with pytest.raises(ValidationError):
        CounterfactualParameters(max_door_open_minutes=125.0)

    # Core lag factor must be between 0.0 and 1.0
    with pytest.raises(ValidationError):
        CounterfactualParameters(core_lag_factor=-0.1)

    with pytest.raises(ValidationError):
        CounterfactualParameters(core_lag_factor=1.1)


def test_reject_extra_and_irrelevant_parameters():
    # Extra unexpected parameter
    with pytest.raises(ValidationError):
        CounterfactualRequest(
            intervention_type="EXPEDITE_DOOR_CLOSING",
            parameters={"extra_unsupported": 123},  # type: ignore
        )

    # Core lag is irrelevant for door closing
    with pytest.raises(ValidationError) as exc:
        CounterfactualRequest(
            intervention_type="EXPEDITE_DOOR_CLOSING",
            parameters=CounterfactualParameters(core_lag_factor=0.5),
        )
    assert "irrelevant for EXPEDITE_DOOR_CLOSING" in str(exc.value)

    # Door minutes is irrelevant for core probe
    with pytest.raises(ValidationError) as exc:
        CounterfactualRequest(
            intervention_type="RELOCATE_LOGGER_DEEP",
            parameters=CounterfactualParameters(max_door_open_minutes=10.0),
        )
    assert "irrelevant for RELOCATE_LOGGER_DEEP" in str(exc.value)

    # Parameters not allowed on interventions without parameters
    with pytest.raises(ValidationError) as exc:
        CounterfactualRequest(
            intervention_type="BACKUP_REEFER_ENGAGED",
            parameters=CounterfactualParameters(max_door_open_minutes=5.0),
        )
    assert "irrelevant" in str(exc.value)


def test_non_default_parameters_change_simulation_results(test_case):
    engine = CounterfactualEngine()

    # Test THERMAL_MASS_CORE_PROBE with low vs high lag factor
    req_low = CounterfactualRequest(
        intervention_type="RELOCATE_LOGGER_DEEP",
        parameters=CounterfactualParameters(core_lag_factor=0.2),
    )
    res_low = engine.simulate(test_case, req_low, "RUN-CF-LOW")

    req_high = CounterfactualRequest(
        intervention_type="RELOCATE_LOGGER_DEEP",
        parameters=CounterfactualParameters(core_lag_factor=0.9),
    )
    res_high = engine.simulate(test_case, req_high, "RUN-CF-HIGH")

    # Higher attenuation factor must produce lower simulated duration or peak
    assert res_high.simulated_excursion_duration_minutes <= res_low.simulated_excursion_duration_minutes
    # Verify exact difference exists
    assert res_low.result_summary != res_high.result_summary


def test_configured_temperature_band_phrasing_without_compliant_limits(test_case):
    engine = CounterfactualEngine()
    req = CounterfactualRequest(
        intervention_type="BACKUP_REEFER_ENGAGED",
    )
    res = engine.simulate(test_case, req, "RUN-PHRASE")
    # Verify phrasing replacement: "configured temperature band" used, "compliant limits" not used
    assert "compliant limits" not in res.result_summary.lower()
    if res.simulated_excursion_duration_minutes == 0.0:
        assert "configured temperature band" in res.result_summary
