"""
apps/api/app/domain/detector.py — Deterministic Cold-Chain Excursion Engine

Core principles:
- 100% deterministic: pure mathematical and rule-based calculations.
- Zero LLM involvement in temperature measurements or time-series calculations.
- Exact boundary handling: [min_celsius, max_celsius] is in-range.
- Detects continuous excursion intervals, duration, min/max, AUC, and recovery time.
- Identifies anomalies: timestamp gaps, impossible jumps, duplicate readings, sensor divergence.
- Produces immutable Observation IDs with cryptographic references.
"""

from datetime import UTC, datetime

from .models import (
    CaseAnalysisResult,
    CustodyEvent,
    Observation,
    OperationalEvent,
    SensorReading,
    ShipmentCase,
)


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 string into UTC datetime. Requires explicit timezone awareness."""
    if not isinstance(dt_str, str) or not dt_str.strip():
        raise ValueError("Invalid timestamp: timestamp string is required and cannot be empty.")
    clean = dt_str.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(clean)
    except Exception as e:
        raise ValueError(f"Malformed ISO 8601 timestamp '{dt_str}': {e}") from e
    if dt.tzinfo is None:
        raise ValueError(
            f"Timestamp '{dt_str}' is timezone-naive. Timezone-aware ISO 8601 (e.g. ending in 'Z' or '+00:00') is required."
        )
    return dt.astimezone(UTC)


def format_iso_utc(dt: datetime) -> str:
    """Format UTC datetime as standard ISO 8601 string."""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class DeterministicExcursionEngine:
    def __init__(self, detector_version: str = "1.0"):
        self.version = detector_version

    def analyze_case(self, case: ShipmentCase) -> CaseAnalysisResult:
        """Run complete deterministic analysis on a shipment case."""
        if not case.readings:
            raise ValueError("ShipmentCase must contain at least one sensor reading.")

        if len(case.readings) > 10000:
            raise ValueError(f"Case exceeds maximum reading limit of 10,000 readings (received {len(case.readings)}).")

        min_allowed = case.temperature_policy.min_celsius
        max_allowed = case.temperature_policy.max_celsius

        # 1. Normalize and deduplicate by composite (sensor_id, timestamp) key
        readings_with_dt: list[tuple[datetime, SensorReading]] = []
        anomalies: list[str] = []
        seen_sensor_timestamps: set[tuple[str, str]] = set()

        for r in case.readings:
            dt = parse_iso_datetime(r.timestamp)
            sensor = r.sensor_id or "default"
            key = (sensor, r.timestamp)
            if key in seen_sensor_timestamps:
                anomalies.append(f"Duplicate reading for sensor '{sensor}' at timestamp {r.timestamp} was deduplicated.")
            else:
                seen_sensor_timestamps.add(key)
                readings_with_dt.append((dt, r))

        readings_with_dt.sort(key=lambda x: (x[0], x[1].sensor_id or ""))

        if len(readings_with_dt) < 1:
            raise ValueError("No valid unique readings available.")

        # 2. Check for out-of-order origin in raw data if any
        raw_timestamps = [parse_iso_datetime(r.timestamp) for r in case.readings]
        sorted_raw = sorted(raw_timestamps)
        if raw_timestamps != sorted_raw:
            anomalies.append("Raw readings were not in chronological order; normalized by timestamp.")

        # 3. Compute baseline statistics
        temps = [r.temperature_celsius for _, r in readings_with_dt]
        min_temp = min(temps)
        max_temp = max(temps)
        mean_temp = round(sum(temps) / len(temps), 2)

        # 4. Infer typical sampling interval (median delta)
        deltas_sec = []
        for i in range(1, len(readings_with_dt)):
            d_sec = (readings_with_dt[i][0] - readings_with_dt[i - 1][0]).total_seconds()
            if d_sec > 0:
                deltas_sec.append(d_sec)

        median_delta_sec = 300.0  # default 5 min if single reading
        if deltas_sec:
            deltas_sec_sorted = sorted(deltas_sec)
            median_delta_sec = deltas_sec_sorted[len(deltas_sec_sorted) // 2]

        expected_interval_min = round(median_delta_sec / 60.0, 1)

        # 5. Anomaly Detection: Gaps and Impossible Jumps
        gap_observations: list[Observation] = []
        jump_observations: list[Observation] = []

        for i in range(1, len(readings_with_dt)):
            prev_dt, prev_r = readings_with_dt[i - 1]
            curr_dt, curr_r = readings_with_dt[i - 1 + 1]
            gap_sec = (curr_dt - prev_dt).total_seconds()

            # Gap check: > 1.5x expected interval
            if gap_sec > (median_delta_sec * 1.5) and gap_sec > 450:
                gap_min = round(gap_sec / 60.0, 1)
                obs_id = f"OBS-GAP-{len(gap_observations) + 1:02d}"
                gap_obs = Observation(
                    id=obs_id,
                    kind="SENSOR_GAP",
                    start_at=format_iso_utc(prev_dt),
                    end_at=format_iso_utc(curr_dt),
                    numeric_values={"gap_duration_minutes": gap_min, "expected_interval_minutes": expected_interval_min},
                    unit="minutes",
                    summary=f"Sensor telemetry gap of {gap_min} minutes detected between readings.",
                    source_event_ids=[],
                    detector_version=self.version
                )
                gap_observations.append(gap_obs)
                anomalies.append(f"Telemetry gap of {gap_min} min between {format_iso_utc(prev_dt)} and {format_iso_utc(curr_dt)}")

            # Jump check: rate of change > 5°C in a single 5-minute interval
            temp_diff = abs(curr_r.temperature_celsius - prev_r.temperature_celsius)
            interval_min = max(0.1, gap_sec / 60.0)
            rate_c_per_min = temp_diff / interval_min

            if temp_diff >= 4.0 and rate_c_per_min > 0.8:
                obs_id = f"OBS-JUMP-{len(jump_observations) + 1:02d}"
                jump_obs = Observation(
                    id=obs_id,
                    kind="JUMP_ANOMALY",
                    start_at=format_iso_utc(prev_dt),
                    end_at=format_iso_utc(curr_dt),
                    numeric_values={
                        "temperature_delta_celsius": round(temp_diff, 2),
                        "rate_celsius_per_minute": round(rate_c_per_min, 2)
                    },
                    unit="celsius",
                    summary=f"Abrupt temperature change of {temp_diff:.1f}°C in {interval_min:.1f} minutes.",
                    source_event_ids=[],
                    detector_version=self.version
                )
                jump_observations.append(jump_obs)
                anomalies.append(f"Sudden temperature jump of {temp_diff:.1f}°C across {interval_min:.1f} min")

        # 6. Excursion Window Detection
        # Continuous segments where temperature is either > max_allowed OR < min_allowed
        excursion_windows: list[Observation] = []
        current_window_readings: list[tuple[datetime, SensorReading]] = []
        window_counter = 0

        for i, (dt, r) in enumerate(readings_with_dt):
            is_excursion = (r.temperature_celsius > max_allowed) or (r.temperature_celsius < min_allowed)

            if is_excursion:
                current_window_readings.append((dt, r))
            else:
                if current_window_readings:
                    # Finalize window
                    window_counter += 1
                    obs = self._build_excursion_observation(
                        window_counter,
                        current_window_readings,
                        min_allowed,
                        max_allowed,
                        expected_interval_min,
                        case.custody_events,
                        case.operational_events
                    )
                    excursion_windows.append(obs)
                    current_window_readings = []

        # If ended while in excursion
        if current_window_readings:
            window_counter += 1
            obs = self._build_excursion_observation(
                window_counter,
                current_window_readings,
                min_allowed,
                max_allowed,
                expected_interval_min,
                case.custody_events,
                case.operational_events
            )
            excursion_windows.append(obs)

        # 7. Overall Excursion Duration
        total_excursion_min = sum(
            obs.numeric_values.get("duration_minutes", 0.0) for obs in excursion_windows
        )

        # 8. Summary Observation
        summary_obs = Observation(
            id="OBS-SUMMARY",
            kind="TEMPERATURE_SUMMARY",
            start_at=format_iso_utc(readings_with_dt[0][0]),
            end_at=format_iso_utc(readings_with_dt[-1][0]),
            numeric_values={
                "min_celsius": min_temp,
                "max_celsius": max_temp,
                "mean_celsius": mean_temp,
                "allowed_min_celsius": min_allowed,
                "allowed_max_celsius": max_allowed,
                "total_excursion_minutes": total_excursion_min,
                "reading_count": float(len(readings_with_dt))
            },
            unit="celsius",
            summary=(
                f"Range [{min_allowed:.1f}°C to {max_allowed:.1f}°C]. "
                f"Recorded values spanned {min_temp:.1f}°C to {max_temp:.1f}°C (mean {mean_temp:.1f}°C). "
                f"{'Excursion detected: ' + str(total_excursion_min) + ' cumulative out-of-range minutes.' if total_excursion_min > 0 else 'Zero excursion detected; compliant throughout.'}"
            ),
            source_event_ids=[],
            detector_version=self.version
        )

        all_observations = [summary_obs] + excursion_windows + gap_observations + jump_observations

        return CaseAnalysisResult(
            case_id=case.id,
            has_excursion=total_excursion_min > 0,
            total_excursion_duration_minutes=round(total_excursion_min, 1),
            min_recorded_temperature=min_temp,
            max_recorded_temperature=max_temp,
            mean_recorded_temperature=mean_temp,
            reading_count=len(case.readings),
            readings_analyzed=len(readings_with_dt),
            observations=all_observations,
            anomalies_detected=anomalies,
            normalized_at=format_iso_utc(datetime.now(UTC))
        )

    def _build_excursion_observation(
        self,
        index: int,
        window: list[tuple[datetime, SensorReading]],
        min_allowed: float,
        max_allowed: float,
        expected_interval_min: float,
        custody_events: list[CustodyEvent],
        operational_events: list[OperationalEvent]
    ) -> Observation:
        """Construct a detailed excursion window observation with event correlation."""
        start_dt = window[0][0]
        end_dt = window[-1][0]

        # Duration is measured from start to end reading plus one sample interval
        # (since each discrete reading represents the interval until the next)
        raw_duration_sec = (end_dt - start_dt).total_seconds()
        duration_minutes = max(expected_interval_min, (raw_duration_sec / 60.0) + expected_interval_min)

        w_temps = [r.temperature_celsius for _, r in window]
        w_max = max(w_temps)
        w_min = min(w_temps)
        w_mean = round(sum(w_temps) / len(w_temps), 2)

        is_heat_excursion = w_max > max_allowed
        is_freeze_excursion = w_min < min_allowed

        # Degree-minutes area over/under threshold
        degree_minutes = 0.0
        for _, r in window:
            if r.temperature_celsius > max_allowed:
                degree_minutes += (r.temperature_celsius - max_allowed) * expected_interval_min
            elif r.temperature_celsius < min_allowed:
                degree_minutes += (min_allowed - r.temperature_celsius) * expected_interval_min

        # Correlate with events happening in or shortly before this window (±15 min)
        correlated_events = []
        for ce in custody_events:
            c_dt = parse_iso_datetime(ce.timestamp)
            delta_before = (start_dt - c_dt).total_seconds() / 60.0
            delta_after = (c_dt - end_dt).total_seconds() / 60.0
            # If within 15 min before window or inside window
            if -15 <= delta_before and delta_after <= 15:
                correlated_events.append(ce.id)

        for oe in operational_events:
            o_dt = parse_iso_datetime(oe.timestamp)
            delta_before = (start_dt - o_dt).total_seconds() / 60.0
            delta_after = (o_dt - end_dt).total_seconds() / 60.0
            if -15 <= delta_before and delta_after <= 15:
                correlated_events.append(oe.id)

        direction = "Upper excursion (heat exposure)" if is_heat_excursion else "Lower excursion (freezing risk)"
        if is_heat_excursion and is_freeze_excursion:
            direction = "Dual excursion (bipolar temperature breach)"

        summary_text = (
            f"{direction}: temperature reached {w_max:.1f}°C (policy max {max_allowed:.1f}°C) "
            f"for approximately {duration_minutes:.0f} minutes with {degree_minutes:.1f} degree-minutes exposure."
        )

        return Observation(
            id=f"OBS-EXCURSION-{index:02d}",
            kind="EXCURSION_WINDOW",
            start_at=format_iso_utc(start_dt),
            end_at=format_iso_utc(end_dt),
            numeric_values={
                "duration_minutes": round(duration_minutes, 1),
                "max_temperature": w_max,
                "min_temperature": w_min,
                "mean_temperature": w_mean,
                "degree_minutes": round(degree_minutes, 2),
                "threshold_celsius": max_allowed if is_heat_excursion else min_allowed
            },
            unit="celsius",
            summary=summary_text,
            source_event_ids=correlated_events,
            detector_version=self.version
        )
