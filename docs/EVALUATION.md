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

| Scenario File | Name & Physical Test Condition | Expected Breach | Duration | Peak Temp | Deterministic Pass |
|:---|:---|:---:|:---:|:---:|:---:|
| `01_door_left_open.json` | Cross-Dock Door Extended Exposure | True | 40.0 min | 11.3°C | **PASS** |
| `02_transfer_delay.json` | Unrefrigerated Staging Delay | True | 60.0 min | 9.2°C | **PASS** |
| `03_reefer_power_loss.json` | Reefer Unit Compressor Shutdown | True | 60.0 min | 15.9°C | **PASS** |
| `04_equipment_drift.json` | Gradual Sensor Calibration Drift | True | 100.0 min | 9.6°C | **PASS** |
| `05_isolated_logger_spike.json` | Transient Heat Pulse Spike | True | 5.0 min | 14.8°C | **PASS** |
| `06_logger_placement_diff.json` | Pallet Exterior vs Interior Gradient | True | 30.0 min | 8.8°C | **PASS** |
| `07_clock_timezone_mismatch.json` | Timezone Offset Ingestion | True | 35.0 min | 9.4°C | **PASS** |
| `08_missing_reading_gap.json` | Sensor Telemetry Missing Gap | False | 0.0 min | 4.5°C | **PASS** |
| `09_dual_cause_event.json` | Compound Door Open + Traffic Delay | True | 65.0 min | 11.5°C | **PASS** |
| `10_no_true_excursion.json` | Fully Compliant Cold-Chain Run | False | 0.0 min | 4.9°C | **PASS** |
| `11_ambiguous_evidence.json` | Borderline Threshold Oscillations | True | 30.0 min | 9.8°C | **PASS** |
| `12_adversarial_prompt_injection.json` | Hostile Injected Telemetry Payload | True | 45.0 min | 12.5°C | **PASS** |

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
