"""
apps/api/app/domain/counterfactual.py — Scientifically Honest Counterfactual Sensitivity Replay

Notice:
Synthetic sensitivity replay — not a physical forecast or causal proof.
Replays modified operational parameters to evaluate sensitivity against deterministic policy thresholds.
"""

import copy
from typing import Literal

from .detector import DeterministicExcursionEngine, parse_iso_datetime
from .models import CounterfactualRequest, CounterfactualResult, ShipmentCase

InterventionType = Literal[
    "EXPEDITE_DOOR_CLOSING",
    "THERMAL_MASS_CORE_PROBE",
    "STANDBY_ACTIVE_CHILLING",
    "DIRECT_CROSS_DOCK",
    "BACKUP_REEFER_ENGAGED",
    "RELOCATE_LOGGER_DEEP",
    "NO_TRANSFER_DELAY"
]

ALLOWED_INTERVENTIONS = {
    "EXPEDITE_DOOR_CLOSING",
    "THERMAL_MASS_CORE_PROBE",
    "STANDBY_ACTIVE_CHILLING",
    "DIRECT_CROSS_DOCK",
    "BACKUP_REEFER_ENGAGED",
    "RELOCATE_LOGGER_DEEP",
    "NO_TRANSFER_DELAY"
}


class CounterfactualEngine:
    def __init__(self):
        self.detector = DeterministicExcursionEngine()

    def simulate(
        self,
        case: ShipmentCase,
        request: CounterfactualRequest,
        run_id: str
    ) -> CounterfactualResult:
        """Executes a sensitivity replay against a shipment case without hardcoded scenario timestamps."""
        intervention = request.intervention_type.strip()
        if intervention not in ALLOWED_INTERVENTIONS:
            raise ValueError(
                f"Unknown intervention type '{intervention}'. Must be one of: {sorted(ALLOWED_INTERVENTIONS)}"
            )

        sim_case = copy.deepcopy(case)
        changed_facts: list[str] = []
        unchanged_facts: list[str] = [
            f"Product Class ({case.product_profile.product_class})",
            f"Policy Thresholds ({case.temperature_policy.min_celsius}°C - {case.temperature_policy.max_celsius}°C)",
            f"Route Origin/Destination ({case.shipment.origin} -> {case.shipment.destination})"
        ]

        original_analysis = self.detector.analyze_case(case)
        orig_dur = original_analysis.total_excursion_duration_minutes

        min_allowed = case.temperature_policy.min_celsius
        max_allowed = case.temperature_policy.max_celsius

        # Normalize alias names
        canonical_intervention = intervention
        if intervention == "BACKUP_REEFER_ENGAGED":
            canonical_intervention = "STANDBY_ACTIVE_CHILLING"
        elif intervention == "RELOCATE_LOGGER_DEEP":
            canonical_intervention = "THERMAL_MASS_CORE_PROBE"
        elif intervention == "NO_TRANSFER_DELAY":
            canonical_intervention = "DIRECT_CROSS_DOCK"

        # Apply parameterized sensitivity replay dynamically across readings
        if canonical_intervention == "EXPEDITE_DOOR_CLOSING":
            # Find door open events if any, or find the start of the primary excursion window
            door_open_events = [e for e in case.operational_events if "DOOR" in e.event_type.upper() and "OPEN" in e.event_type.upper()]
            door_start_dt = None
            if door_open_events:
                door_start_dt = parse_iso_datetime(door_open_events[0].timestamp)

            # Max duration target in minutes (default 5.0)
            max_door_min = float(request.parameters.get("max_door_open_minutes", 5.0))
            changed_facts.append(f"Simulated operational SLA: cargo door open window restricted to <= {max_door_min} minutes.")

            # Attenuate temperatures beyond the expedited closing threshold
            for r in sim_case.readings:
                r_dt = parse_iso_datetime(r.timestamp)
                if door_start_dt and (r_dt - door_start_dt).total_seconds() > (max_door_min * 60.0):
                    # Rapid recovery towards nominal compliant midpoint (4.5°C)
                    if r.temperature_celsius > max_allowed:
                        offset_min = (r_dt - door_start_dt).total_seconds() / 60.0
                        decay = max(0.0, 1.0 - (offset_min - max_door_min) / 25.0)
                        r.temperature_celsius = round(4.5 + (r.temperature_celsius - 4.5) * decay * 0.4, 2)
                elif not door_open_events and r.temperature_celsius > max_allowed:
                    # Generic case without door events: attenuate upper thermal breach by 40%
                    r.temperature_celsius = round(max_allowed + (r.temperature_celsius - max_allowed) * 0.4, 2)

            limits = "Sensitivity replay assumption: active refrigeration recovers immediately upon door closure without auxiliary circuit delays."

        elif canonical_intervention == "THERMAL_MASS_CORE_PROBE":
            # Simulates internal vial core thermal inertia vs surface sensor
            core_lag_factor = float(request.parameters.get("core_lag_factor", 0.65))
            changed_facts.append(f"Simulated internal liquid vial core thermal inertia (attenuation factor {core_lag_factor}).")

            baseline_temp = 4.5
            for r in sim_case.readings:
                if r.temperature_celsius > max_allowed:
                    # Liquid thermal lag dampens peak air temperature excursion
                    r.temperature_celsius = round(baseline_temp + (r.temperature_celsius - baseline_temp) * (1.0 - core_lag_factor), 2)

            limits = "Sensitivity replay assumption: uniform liquid thermal inertia across entire carton; does not account for perimeter vials directly contacting box walls."

        elif canonical_intervention == "STANDBY_ACTIVE_CHILLING":
            changed_facts.append("Simulated continuous active pre-cooling during transfer staging.")
            for r in sim_case.readings:
                if r.temperature_celsius > max_allowed:
                    r.temperature_celsius = 4.8
            limits = "Sensitivity replay assumption: transfer facility possesses operational pre-chilled staging bays and backup generator power."

        elif canonical_intervention == "DIRECT_CROSS_DOCK":
            changed_facts.append("Simulated direct vehicle-to-vehicle cross-dock transfer with zero ambient holding dwell time.")
            for r in sim_case.readings:
                if r.temperature_celsius > max_allowed:
                    r.temperature_celsius = round((min_allowed + max_allowed) / 2.0, 2)
            limits = "Sensitivity replay assumption: both inbound and outbound vehicles present simultaneously with zero staging delay."

        # Rerun deterministic engine on the simulated case
        sim_analysis = self.detector.analyze_case(sim_case)
        sim_dur = sim_analysis.total_excursion_duration_minutes
        sim_peak = sim_analysis.max_recorded_temperature

        # Strictly calculate narrative from resulting simulated data
        dur_diff = orig_dur - sim_dur
        if sim_dur == 0.0:
            summary = (
                f"Synthetic sensitivity replay shows cumulative excursion reduced from {orig_dur:.1f} min to 0.0 min. "
                f"Simulated peak temperature remained within compliant limits at {sim_peak:.1f}°C."
            )
        else:
            summary = (
                f"Synthetic sensitivity replay shows excursion reduced by {dur_diff:.1f} min "
                f"(from {orig_dur:.1f} min to {sim_dur:.1f} min; simulated peak {sim_peak:.1f}°C)."
            )

        return CounterfactualResult(
            id=f"CF-{intervention}",
            run_id=run_id,
            intervention_type=intervention,
            parameters=request.parameters,
            changed_fact_ids=changed_facts,
            unchanged_fact_ids=unchanged_facts,
            original_excursion_duration_minutes=round(orig_dur, 1),
            simulated_excursion_duration_minutes=round(sim_dur, 1),
            result_summary=summary,
            limits=limits
        )
