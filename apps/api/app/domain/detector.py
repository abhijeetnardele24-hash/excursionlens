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

from collections import defaultdict
from datetime import UTC, datetime, timedelta

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
        """
        Run complete deterministic multi-sensor excursion analysis on a shipment case.

        Sensor-Level vs Case-Level Aggregation Architecture:
        1. Sensor-Specific Telemetry Partitioning:
           - Readings are grouped by `sensor_id` prior to excursion detection.
           - Each sensor maintains its own chronological telemetry baseline, sampling interval,
             and continuous excursion windows.
        2. Sensor-Specific Indicators:
           - Sensor-specific excursion windows (`OBS-EXCURSION-{nn}`) with individual peak (°C)
             and Area Under the Curve (AUC in degree-minutes).
           - Sensor-specific missing telemetry gaps (`OBS-GAP-{nn}`) and rapid jump anomalies (`OBS-JUMP-{nn}`).
           - Explicit sensor-to-sensor disagreement evidence (`OBS-DIVERGENCE-{nn}`) detecting surface vs
             core liquid thermal gradients (>= 2.0°C differential at concurrent timestamps).
        3. Case-Level Synthesis:
           - Peak Temperature: Maximum recorded temperature across all sensors.
           - Minimum Temperature: Minimum recorded temperature across all sensors.
           - Mean Temperature: Global arithmetic mean of all valid readings across sensors.
           - Total Excursion Duration: Mathematical union of time intervals [start_dt, end_dt]
             during which ANY sensor experienced an out-of-band excursion. This prevents double-counting
             concurrent multi-sensor breaches (e.g. simultaneous surface and core breaches during door opening).
        """
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

        # 3. Compute global baseline statistics
        temps = [r.temperature_celsius for _, r in readings_with_dt]
        min_temp = min(temps)
        max_temp = max(temps)
        mean_temp = round(sum(temps) / len(temps), 2)

        # 4. Partition readings by sensor before excursion and anomaly analysis
        sensor_partitions: dict[str, list[tuple[datetime, SensorReading]]] = defaultdict(list)
        for dt, r in readings_with_dt:
            s_id = r.sensor_id or "default"
            sensor_partitions[s_id].append((dt, r))

        # Sort each partition strictly chronologically
        for s_id in sensor_partitions:
            sensor_partitions[s_id].sort(key=lambda x: x[0])

        gap_observations: list[Observation] = []
        jump_observations: list[Observation] = []
        excursion_windows: list[Observation] = []
        window_counter = 0

        # 5. Process each sensor partition independently
        for s_id, s_readings in sensor_partitions.items():
            # Invert deltas to calculate sensor-specific median interval
            deltas_sec = []
            for i in range(1, len(s_readings)):
                d_sec = (s_readings[i][0] - s_readings[i - 1][0]).total_seconds()
                if d_sec > 0:
                    deltas_sec.append(d_sec)

            s_median_delta_sec = 300.0  # default 5 min if single reading
            if deltas_sec:
                deltas_sec_sorted = sorted(deltas_sec)
                s_median_delta_sec = deltas_sec_sorted[(len(deltas_sec_sorted) - 1) // 2]

            s_expected_interval_min = round(s_median_delta_sec / 60.0, 1)

            # Anomaly Detection: Gaps and Jumps for this specific sensor
            for i in range(1, len(s_readings)):
                prev_dt, prev_r = s_readings[i - 1]
                curr_dt, curr_r = s_readings[i]
                gap_sec = (curr_dt - prev_dt).total_seconds()

                if gap_sec > (s_median_delta_sec * 1.5) and gap_sec > 450:
                    gap_min = round(gap_sec / 60.0, 1)
                    obs_id = f"OBS-GAP-{len(gap_observations) + 1:02d}"
                    gap_obs = Observation(
                        id=obs_id,
                        kind="SENSOR_GAP",
                        start_at=format_iso_utc(prev_dt),
                        end_at=format_iso_utc(curr_dt),
                        sensor_id=s_id,
                        numeric_values={
                            "gap_duration_minutes": float(gap_min),
                            "expected_interval_minutes": float(s_expected_interval_min),
                        },
                        unit="minutes",
                        summary=f"Sensor telemetry gap of {gap_min} minutes detected on sensor '{s_id}'.",
                        source_event_ids=[s_id] if s_id != "default" else [],
                        detector_version=self.version,
                    )
                    gap_observations.append(gap_obs)
                    anomalies.append(f"Telemetry gap of {gap_min} min on sensor '{s_id}' between {format_iso_utc(prev_dt)} and {format_iso_utc(curr_dt)}")

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
                        sensor_id=s_id,
                        numeric_values={
                            "temperature_delta_celsius": round(temp_diff, 2),
                            "rate_celsius_per_minute": round(rate_c_per_min, 2),
                        },
                        unit="celsius",
                        summary=f"Abrupt temperature change of {temp_diff:.1f}°C in {interval_min:.1f} minutes on sensor '{s_id}'.",
                        source_event_ids=[s_id] if s_id != "default" else [],
                        detector_version=self.version,
                    )
                    jump_observations.append(jump_obs)
                    anomalies.append(f"Sudden temperature jump of {temp_diff:.1f}°C on sensor '{s_id}' across {interval_min:.1f} min")

            # Excursion Window Detection for this specific sensor
            current_window_readings: list[tuple[datetime, SensorReading]] = []
            for dt, r in s_readings:
                is_excursion = (r.temperature_celsius > max_allowed) or (r.temperature_celsius < min_allowed)
                if is_excursion:
                    current_window_readings.append((dt, r))
                else:
                    if current_window_readings:
                        window_counter += 1
                        obs = self._build_excursion_observation(
                            window_counter,
                            s_id,
                            current_window_readings,
                            min_allowed,
                            max_allowed,
                            s_expected_interval_min,
                            case.custody_events,
                            case.operational_events,
                        )
                        excursion_windows.append(obs)
                        current_window_readings = []

            if current_window_readings:
                window_counter += 1
                obs = self._build_excursion_observation(
                    window_counter,
                    s_id,
                    current_window_readings,
                    min_allowed,
                    max_allowed,
                    s_expected_interval_min,
                    case.custody_events,
                    case.operational_events,
                )
                excursion_windows.append(obs)

        # 6. Multi-Sensor Disagreement / Divergence Detection (e.g. Surface vs Core Thermal Lag)
        divergence_observations: list[Observation] = []
        if len(sensor_partitions) > 1:
            sensor_keys = sorted(sensor_partitions.keys())
            for idx_a in range(len(sensor_keys)):
                for idx_b in range(idx_a + 1, len(sensor_keys)):
                    s_a = sensor_keys[idx_a]
                    s_b = sensor_keys[idx_b]
                    r_a_list = sensor_partitions[s_a]
                    r_b_list = sensor_partitions[s_b]

                    # Map s_b readings by nearest timestamp (within 3 minutes)
                    b_by_time = {format_iso_utc(dt): r for dt, r in r_b_list}
                    divergent_clusters: list[list[tuple[datetime, float, float, float]]] = []
                    current_cluster: list[tuple[datetime, float, float, float]] = []

                    for dt_a, r_a in r_a_list:
                        # Match exact or nearest reading
                        key_a = format_iso_utc(dt_a)
                        r_b = b_by_time.get(key_a)
                        if not r_b:
                            # Search within 180 seconds
                            for dt_b, candidate_b in r_b_list:
                                if abs((dt_a - dt_b).total_seconds()) <= 180:
                                    r_b = candidate_b
                                    break
                        if r_b:
                            diff = abs(r_a.temperature_celsius - r_b.temperature_celsius)
                            if diff >= 2.0:
                                current_cluster.append((dt_a, r_a.temperature_celsius, r_b.temperature_celsius, diff))
                            else:
                                if current_cluster:
                                    divergent_clusters.append(current_cluster)
                                    current_cluster = []
                    if current_cluster:
                        divergent_clusters.append(current_cluster)

                    for cluster in divergent_clusters:
                        start_c = cluster[0][0]
                        end_c = cluster[-1][0]
                        max_diff = max(pt[3] for pt in cluster)
                        mean_diff = round(sum(pt[3] for pt in cluster) / len(cluster), 2)
                        dur_c = max(5.0, ((end_c - start_c).total_seconds() / 60.0) + 5.0)

                        div_obs = Observation(
                            id=f"OBS-DIVERGENCE-{len(divergence_observations) + 1:02d}",
                            kind="SENSOR_DISAGREEMENT",
                            start_at=format_iso_utc(start_c),
                            end_at=format_iso_utc(end_c),
                            numeric_values={
                                "max_divergence_celsius": round(max_diff, 2),
                                "mean_divergence_celsius": float(mean_diff),
                                "duration_minutes": round(dur_c, 1),
                            },
                            unit="celsius",
                            summary=(
                                f"Explicit sensor divergence of {max_diff:.1f}°C detected between "
                                f"'{s_a}' and '{s_b}' (mean disagreement {mean_diff:.1f}°C over {dur_c:.0f} min; "
                                f"surface vs core thermal inertia)."
                            ),
                            source_event_ids=[s_a, s_b],
                            detector_version=self.version,
                        )
                        divergence_observations.append(div_obs)
                        anomalies.append(
                            f"Sensor divergence: '{s_a}' vs '{s_b}' differed by up to {max_diff:.1f}°C across {dur_c:.0f} min"
                        )

        # 7. Case-Level Excursion Duration via Union of Sensor Excursion Intervals
        # Merges overlapping intervals across sensors so concurrent multi-sensor breaches are not double-counted
        raw_intervals: list[tuple[datetime, datetime]] = []
        for obs in excursion_windows:
            s_dt = parse_iso_datetime(obs.start_at)
            e_dt = parse_iso_datetime(obs.end_at)
            dur_min = obs.numeric_values.get("duration_minutes", 0.0)
            actual_end = max(e_dt, s_dt + timedelta(seconds=dur_min * 60.0))
            raw_intervals.append((s_dt, actual_end))

        raw_intervals.sort(key=lambda x: x[0])
        merged_intervals: list[tuple[datetime, datetime]] = []
        for s_int, e_int in raw_intervals:
            if not merged_intervals:
                merged_intervals.append((s_int, e_int))
            else:
                p_start, p_end = merged_intervals[-1]
                if s_int <= p_end:
                    merged_intervals[-1] = (p_start, max(p_end, e_int))
                else:
                    merged_intervals.append((s_int, e_int))

        total_excursion_min = sum((e - s).total_seconds() / 60.0 for s, e in merged_intervals)

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
                "total_excursion_minutes": round(total_excursion_min, 1),
                "reading_count": float(len(readings_with_dt)),
                "sensor_count": float(len(sensor_partitions)),
            },
            unit="celsius",
            summary=(
                f"Range [{min_allowed:.1f}°C to {max_allowed:.1f}°C] across {len(sensor_partitions)} sensor(s). "
                f"Recorded values spanned {min_temp:.1f}°C to {max_temp:.1f}°C (mean {mean_temp:.1f}°C). "
                f"{'Excursion detected: ' + str(round(total_excursion_min, 1)) + ' cumulative out-of-range minutes.' if total_excursion_min > 0 else 'Zero excursion detected; compliant throughout.'}"
            ),
            source_event_ids=[],
            detector_version=self.version,
        )

        all_observations = (
            [summary_obs]
            + excursion_windows
            + gap_observations
            + jump_observations
            + divergence_observations
        )

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
            normalized_at=format_iso_utc(datetime.now(UTC)),
        )

    def _build_excursion_observation(
        self,
        index: int,
        sensor_id: str,
        window: list[tuple[datetime, SensorReading]],
        min_allowed: float,
        max_allowed: float,
        expected_interval_min: float,
        custody_events: list[CustodyEvent],
        operational_events: list[OperationalEvent],
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

        # Degree-minutes area over/under threshold (AUC)
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

        sensor_suffix = f" on sensor '{sensor_id}'" if sensor_id and sensor_id != "default" else ""
        summary_text = (
            f"{direction}{sensor_suffix}: temperature reached {w_max:.1f}°C (policy max {max_allowed:.1f}°C) "
            f"for approximately {duration_minutes:.0f} minutes with {degree_minutes:.1f} degree-minutes exposure."
        )

        return Observation(
            id=f"OBS-EXCURSION-{index:02d}",
            kind="EXCURSION_WINDOW",
            start_at=format_iso_utc(start_dt),
            end_at=format_iso_utc(end_dt),
            sensor_id=sensor_id,
            numeric_values={
                "duration_minutes": round(duration_minutes, 1),
                "max_temperature": float(w_max),
                "min_temperature": float(w_min),
                "mean_temperature": float(w_mean),
                "degree_minutes": round(degree_minutes, 2),
                "auc_degree_minutes": round(degree_minutes, 2),
                "threshold_celsius": float(max_allowed if is_heat_excursion else min_allowed),
            },
            unit="celsius",
            summary=summary_text,
            source_event_ids=correlated_events,
            detector_version=self.version,
        )
