"""
benchmark/run_benchmark.py — Reproducible Benchmark Runner for ExcursionLens

Evaluates deterministic excursion detection and anomaly verification across
all 12 frozen synthetic scenarios against benchmark_expectations.json.

Emits structured machine-readable results to test-results/benchmark-results.json.
"""

import json
import os
import sys
import time

from apps.api.app.domain.detector import DeterministicExcursionEngine
from apps.api.app.domain.models import ShipmentCase


def run_benchmark() -> int:
    start_time = time.time()
    scenarios_dir = "benchmark/scenarios"
    expectations_file = "benchmark/expected/benchmark_expectations.json"

    if not os.path.exists(expectations_file):
        print(f"❌ Missing expectations file: {expectations_file}")
        return 1

    with open(expectations_file, "r", encoding="utf-8") as f:
        expectations = json.load(f)

    engine = DeterministicExcursionEngine()
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_scenarios": len(expectations),
        "passed_scenarios": 0,
        "failed_scenarios": 0,
        "scenarios": {},
        "benchmark_duration_ms": 0
    }

    print("=" * 70)
    print("📊 Running ExcursionLens Frozen Benchmark Suite (12 Scenarios)")
    print("=" * 70)

    for case_id, exp in expectations.items():
        filename = exp["filename"]
        filepath = os.path.join(scenarios_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                case_data = json.load(f)

            case = ShipmentCase.model_validate(case_data)
            analysis = engine.analyze_case(case)

            # Assert exact match against expectations
            excursion_match = (analysis.has_excursion == exp["has_excursion"])
            duration_match = abs(analysis.total_excursion_duration_minutes - exp["total_excursion_duration_minutes"]) < 0.1
            max_temp_match = abs(analysis.max_recorded_temperature - exp["max_temperature"]) < 0.1
            obs_match = (len(analysis.observations) == exp["observation_count"])

            passed = excursion_match and duration_match and max_temp_match and obs_match

            if passed:
                results["passed_scenarios"] += 1
                status = "PASS"
                icon = "✅"
            else:
                results["failed_scenarios"] += 1
                status = "FAIL"
                icon = "❌"

            results["scenarios"][case_id] = {
                "filename": filename,
                "status": status,
                "has_excursion": analysis.has_excursion,
                "duration_minutes": analysis.total_excursion_duration_minutes,
                "max_temperature": analysis.max_recorded_temperature,
                "observations_count": len(analysis.observations),
                "anomalies_detected": analysis.anomalies_detected
            }

            print(f"{icon} [{status}] {filename:35s} | Excursion={analysis.has_excursion!s:5s} | Dur={analysis.total_excursion_duration_minutes:4.1f}m | Max={analysis.max_recorded_temperature:4.1f}°C")

        except Exception as e:
            results["failed_scenarios"] += 1
            results["scenarios"][case_id] = {
                "filename": filename,
                "status": "ERROR",
                "error": str(e)
            }
            print(f"❌ [ERR]  {filename:35s} | Error: {e}")

    duration_ms = int((time.time() - start_time) * 1000)
    results["benchmark_duration_ms"] = duration_ms

    os.makedirs("test-results", exist_ok=True)
    out_file = "test-results/benchmark-results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("=" * 70)
    print(f"Benchmark finished in {duration_ms}ms: {results['passed_scenarios']}/{results['total_scenarios']} passed.")
    print(f"Results recorded at: {out_file}")
    print("=" * 70)

    return 0 if results["failed_scenarios"] == 0 else 1


if __name__ == "__main__":
    sys.exit(run_benchmark())
