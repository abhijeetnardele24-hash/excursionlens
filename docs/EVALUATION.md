# ExcursionLens Benchmark Evaluation & Validation Methodology

## 1. Evaluation Methodology

To validate both the deterministic domain calculations and the agentic causal reasoning without relying on unpredictable live physical shipments, ExcursionLens includes a **Frozen Synthetic Benchmark Suite** of 12 real-world pharmaceutical logistics failure scenarios.

Every scenario includes:
1. Ground-truth telemetry time-series (5-minute reading intervals, ambient temperature, battery voltage, vehicle coordinates).
2. Multimodal custody and operational event logs (dispatch, dock arrival, reefer door opening, cross-dock handoff, receiving).
3. Pre-calculated expected values for:
   - Threshold breach occurrence (`has_excursion`)
   - Duration in minutes (`expected_duration_minutes`)
   - Peak excursion temperature (`expected_peak_celsius`)
   - Mandatory quarantine posture (`QUARANTINE_PENDING_QUALIFIED_REVIEW`)

---

## 2. Benchmark Scenario Matrix (12/12 Verified)

| Scenario ID | Name & Description | Breach Window | Peak Temp | Deterministic Pass |
|:---|:---|:---:|:---:|:---:|
| `SCN-01-NMB-CANONICAL` | Canonical NMB-204 Door Open Staging Breach | 42 min | 10.5°C | **PASS** |
| `SCN-02-OVERNIGHT-CROSSING` | Midnight UTC Date Boundary Transit Leg | 35 min | 9.8°C | **PASS** |
| `SCN-03-REEFER-POWER-LOSS` | Auxiliary Circuit Failure with Voltage Drop | 65 min | 12.4°C | **PASS** |
| `SCN-04-DUPLICATE-READINGS` | Duplicate Timestamps & Logger Retransmit | 40 min | 10.1°C | **PASS** |
| `SCN-05-SENSOR-GAP-MISSING` | Missing 15-Minute Sensor Telemetry Gap | 45 min | 11.2°C | **PASS** |
| `SCN-06-THRESHOLD-BOUNDARY` | Temperature Peaking Exactly at 8.00°C Limit | 0 min | 8.0°C | **PASS** |
| `SCN-07-RAPID-RATE-OF-RISE` | Rapid Thermal Spike (>2.0°C per 5 min) | 25 min | 13.8°C | **PASS** |
| `SCN-08-FREEZING-BREACH` | Sub-Zero Thermal Inversion (<2.0°C) | 30 min | 0.8°C | **PASS** |
| `SCN-09-PROBE-CORE-LAG` | Surface vs. Core Probe Thermal Inertia Lag | 40 min | 10.2°C | **PASS** |
| `SCN-10-MULTI-WINDOW` | Two Distinct Thermal Breaches in One Run | 50 min | 9.9°C | **PASS** |
| `SCN-11-EXTENDED-HEAT` | Long-Duration Ambient Heat Wave Exposure | 120 min | 14.5°C | **PASS** |
| `SCN-12-CORRUPTED-CSV` | Non-Monotonic Timestamps & Jumbled Rows | 35 min | 9.5°C | **PASS** |

### Benchmark Execution Command
```bash
python benchmark/run_benchmark.py
```
**Result:** 12 of 12 scenarios passed with 100% mathematical precision against pre-calculated ground-truth boundaries.

---

## 3. Grounding & Citation Validation Results

The Claims Validator (`apps/api/app/domain/validator.py`) was tested against synthetic adversarial perturbations:
- **Hallucinated Evidence IDs:** Synthetic hypotheses attempting to cite non-existent observation IDs (e.g., `OBS-HALLUCINATED-99`) are automatically rejected.
- **Prohibited Disposition Language:** Any hypothesis containing release assertions ("Product is completely safe for immediate release") is stripped of authority and flagged as a safety violation.
- **Strict Allowlist Compliance:** 100% of external web sources retrieved via Tavily adhere to the domain allowlist (`cdc.gov`, `fda.gov`, `who.int`, `gs1.org`).
