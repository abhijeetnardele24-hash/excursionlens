# ExcursionLens

**Evidence-first operational agent for biopharmaceutical cold-chain temperature excursion forensics.**  
*Designed to use NVIDIA Nemotron through Nebius Token Factory. Current committed execution evidence is fixture mode; live verification remains blocked pending credentials.*

[![Master Verification](https://img.shields.io/badge/Verification%20Suite-INTERNAL%20COMPLETE%20%2F%20ACTION%20REQUIRED-275E4B?style=for-the-badge&logo=checkmarx)](https://github.com/abhijeetnardele24-hash/excursionlens/actions/workflows/ci.yml)
[![Accessibility](https://img.shields.io/badge/Axe%20Accessibility-0%20Violations%20in%20Tested%20States-275E4B?style=for-the-badge&logo=w3c)](tests/e2e/journey.spec.ts)
[![Benchmark](https://img.shields.io/badge/Frozen%20Benchmark-12%2F12%20Scenarios%20(100%25)-275E4B?style=for-the-badge&logo=speedtest)](benchmark/run_benchmark.py)
[![Pytest Coverage](https://img.shields.io/badge/Pytest%20Coverage-92.98%25%20Stmt%20%7C%2081.85%25%20Branch-275E4B?style=for-the-badge&logo=pytest)](apps/api/tests)
[![License](https://img.shields.io/badge/License-Apache--2.0-365E7D?style=for-the-badge)](LICENSE)

> [!NOTE]
> **Submission & Verification Status:** `INTERNAL_COMPLETE_EXTERNAL_ACTION_REQUIRED`  
> All internal code, deterministic algorithms, type checking, security scanning, Playwright E2E suites, Axe accessibility scans, and unit tests are complete and verified. Public deployment is active and verified (`LIVE_DEPLOYED`), while live provider inference remains in deterministic fixture replay mode pending external keys.  
> **Authoritative CI Verification:** Evaluated and verified in the [ExcursionLens GitHub Actions CI Workflow](https://github.com/abhijeetnardele24-hash/excursionlens/actions/workflows/ci.yml) (see [All Workflow Runs](https://github.com/abhijeetnardele24-hash/excursionlens/actions)). Each authoritative CI run evaluates the exact Git commit and publishes a machine-readable downloadable artifact named `verification-artifacts-<COMMIT_SHA>`. Authoritative Linux CI totals: **92.98% statement coverage** (1,471/1,582 statements) and **81.85% unrounded branch coverage** (424/518 branches, $\ge 80.0\%$, 90.24% combined coverage under canonical pytest 9.2.0 on Python 3.11.17 across **165 passed test cases**).


---

## Architecture Overview

![ExcursionLens Architecture](docs/assets/architecture.png)

---

## Hackathon Tracks

- **Primary Track:** *Best Apps and Agents*
- **Bonus Track Status:** *Best Use of Tavily* is omitted / unselected pending provision of a live `TAVILY_API_KEY` (live search receipt required).

---

## The Problem: Cold-Chain Vulnerabilities in Biopharmaceutical Distribution

Temperature-sensitive vaccines, biologics, and biopharmaceuticals depend on continuous thermal integrity (standard 2°C to 8°C controls) across multimodal transit. According to the World Health Organization (WHO), up to 50% of vaccines are wasted globally each year in part due to cold-chain failures, temperature excursions, and logistical bottlenecks (*WHO Immunization Supply Chain Guidelines*).

In life sciences operations:
1. **The Investigation Bottleneck:** When an Internet-of-Things (IoT) temperature logger alarms at receiving dock, operations teams must manually reconcile disjointed sensor logs, delivery manifests, and vehicle telemetry to understand if the breach penetrated the liquid core of the vial or merely warmed surface air during pallet handoff.
2. **Why Generic AI Fails:** Standard unconstrained LLM wrappers are hazardous in regulated operations. They hallucinate approvals, invent regulations, and attempt unauthorized product release determinations.

### The ExcursionLens Solution
ExcursionLens combines a **100% deterministic domain foundation** with **bounded agentic causal reasoning**:
- **Deterministic Core:** Zero AI tokens in temperature calculations. Window detection, 40.0-min duration, 10.5°C peak breach, rate-of-change, and 50.5°C·min Area Under the Curve (AUC) are pure mathematical calculations.
- **Authoritative Grounding:** Integrated search through Tavily restricted to trusted public health domains (`cdc.gov`, `fda.gov`, `who.int`, `gs1.org`). Automated tests strictly enforce domain allowlisting and reject URL spoofing; in offline/demo mode, the system falls back safely to pre-vetted verified fixture summaries.
- **NVIDIA Nemotron via Nebius Token Factory:** Deep causal hypothesis generation across competing operational explanations.
- **Adversarial Skeptic Pass:** An adversarial critique systematically audits hypotheses against physical telemetry (e.g., verifying vehicle bus voltage directly disproves reefer auxiliary power failure).
- **Quality Posture Boundary:** The system is architecturally barred from making final release dispositions. All investigations conclude in `QUARANTINE_PENDING_QUALIFIED_REVIEW` with an auditable human-review packet.

> **Decision-Support Boundary Notice:** ExcursionLens outputs are investigation-support evidence generated from synthetic or user-supplied telemetry. They do not determine product safety, potency, regulatory compliance or disposition. Follow organizational SOPs and obtain review from an authorized quality professional.

---

## Product Screenshots & User Journey

| 01. Case Overview & Deterministic Baseline | 02. Timeline & Telemetry Alignment |
|:---:|:---:|
| [![Case Overview](docs/assets/screenshots/01_case_overview.png)](docs/assets/screenshots/01_case_overview.png) | [![Timeline](docs/assets/screenshots/02_timeline_evidence.png)](docs/assets/screenshots/02_timeline_evidence.png) |
| Ingests raw telemetry and computes breach metrics before any AI invocation. | Correlates 5-min logger readings with custody and door-open events. |

| 03. Competing Hypotheses & Skeptic Pass | 04. Counterfactual Preventive Control |
|:---:|:---:|
| [![Hypotheses](docs/assets/screenshots/03_hypothesis_board.png)](docs/assets/screenshots/03_hypothesis_board.png) | [![Counterfactual](docs/assets/screenshots/04_counterfactual.png)](docs/assets/screenshots/04_counterfactual.png) |
| Nemotron generates 3 competing hypotheses; Skeptic refutes power loss. | Replays synthetic sensitivity controls (e.g. 5-min door limit). |

| 05. Quality Review Packet | Devpost Video Thumbnail |
|:---:|:---:|
| [![Review Packet](docs/assets/screenshots/05_review_packet.png)](docs/assets/screenshots/05_review_packet.png) | [![Devpost Thumbnail](docs/assets/excursionlens-devpost-thumbnail.png)](docs/assets/excursionlens-devpost-thumbnail.png) |
| Printable review packet with cryptographic SHA-256 evidence digests. | Official hackathon submission graphic. |

---

## Judge Quick-Start (< 2 Minutes)

ExcursionLens is engineered to run immediately out-of-the-box. **Zero API keys are required to explore the full canonical NMB-204 case.** When run without keys, the system operates in an honest, transparent `DEMO_FIXTURE` mode with pre-validated synthetic receipts.

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend build)

### 2. Installation & Run
```bash
# Clone the dedicated repository
git clone https://github.com/abhijeetnardele24-hash/excursionlens.git
cd excursionlens

# Install Python backend dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Build the frontend single-page application
cd apps/web
npm install
npm run build
cd ../..

# Start the unified production server
python -m uvicorn apps.api.app.main:app --port 8000 --host 127.0.0.1
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## Live Provider Setup (Nebius Token Factory & Tavily)

To run with live cloud inference and live web searches:
```bash
# Copy template
cp .env.example .env

# Set your API keys in .env
NEBIUS_TOKEN_FACTORY_KEY="your-nebius-token-factory-key"
TAVILY_API_KEY="your-tavily-api-key"

# Verify live provider connectivity (fails closed if keys are absent or invalid)
python scripts/live_smoke.py
```

When valid keys are provided, ExcursionLens queries the live model catalog from Nebius Token Factory (`GET /v1/models`), filters for available NVIDIA/Nemotron models, and routes structured reasoning to the selected model ID. When keys are absent, the application runs transparently in `DEMO_FIXTURE` mode with verified synthetic receipts.

---

## 8-Stage Bounded Investigation State Machine

Investigations stream in real-time over Server-Sent Events (SSE) across eight discrete states:

```
[1. VALIDATE_SCHEMA]    --> Enforces strict Pydantic schemas on custody & sensor logs.
[2. NORMALIZE_SERIES]   --> Detects reading intervals, gaps, and computes rate of temperature rise.
[3. DETECT_EXCURSION]   --> Deterministically calculates breach windows, AUC, and peak breach values.
[4. TAVILY_GUIDANCE]    --> Queries CDC/FDA/WHO guidelines on strict domain allowlist (falls back safely to verified fixture summaries).
[5. NEMOTRON_HYPOTHESIS]--> Generates 3 competing causal hypotheses via Nebius Token Factory.
[6. ADVERSARIAL_SKEPTIC]--> Refutes invalid hypotheses using physical evidence (bus voltage).
[7. VALIDATE_CITATIONS] --> Verifies all factual claims against observation IDs (OBS-* / SRC-*).
[8. REVIEW_PACKET]      --> Compiles quality review packet with cryptographic digests and sensitivity replay.
```

---

## Deterministic Benchmark Results (12/12 Scenarios Verified)

Our frozen synthetic benchmark suite tests edge-case resilience directly against ground-truth physical expectations:

| Scenario File | Scenario Description | Expected Breach | Duration | Peak Temp | Pass Status |
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
| `10_no_true_excursion.json` | Telemetry Within Configured Band | False | 0.0 min | 4.9°C | **PASS** |
| `11_ambiguous_evidence.json` | Borderline Threshold Oscillations | True | 30.0 min | 9.8°C | **PASS** |
| `12_adversarial_prompt_injection.json` | Hostile Injected Telemetry Payload | True | 45.0 min | 12.5°C | **PASS** |

Run the benchmark suite:
```bash
python benchmark/run_benchmark.py
```

---

## Verification & Automated Test Suite

ExcursionLens includes a master verification gate (`scripts/verify.py`) running 7 rigorous validation layers:

```bash
python scripts/verify.py
```

- **Ruff Python Linter:** 0 violations across backend and test files.
- **Python Static Typing (Mypy):** 0 type errors with `--check-untyped-defs`.
- **Frontend Build:** Strict TypeScript check and Vite production bundle.
- **Pytest Suite:** 165 test cases passing with 92.98% statement coverage and 81.85% unrounded branch coverage (90.24% combined coverage under canonical pytest 9.2.0 on Python 3.11.17 with `--cov-branch --cov-fail-under=85` enforcement).
- **Deterministic Benchmark:** 12 of 12 scenarios passing with 100% precision.
- **Security Scanner:** 0 secrets, tokens, or private credentials committed.
- **Playwright E2E & Axe Accessibility:** 5 logical journeys (25 viewport executions) passing across 5 viewports (320px, 390px, 768px, 1280px, 1920px). Automated Axe scans detected zero violations in the tested states across all 5 viewports. (Automated scans verify targeted accessibility criteria and do not constitute complete WCAG certification).

> **Evidence Authority:** The authoritative verification record for each evaluated commit is generated directly within the [GitHub Actions CI Workflow](https://github.com/abhijeetnardele24-hash/excursionlens/actions/workflows/ci.yml) and uploaded as downloadable artifact `verification-artifacts-<COMMIT_SHA>`. Authoritative Linux CI totals: 165 Pytest cases passing, 92.98% statement coverage, and 81.85% unrounded branch coverage (exceeding the strict 80.0% unrounded gate under pytest 9.2.0).


---

## Docker Container & Deployment Posture

ExcursionLens is packaged as a single hardened, multi-stage Docker container running as a non-root application user:

```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

- **Security Hardening:** The runtime container executes as non-root user `appuser` (UID 10001) with dropped capabilities.
- **Deployment Status:** Public deployment is REQUIRED by hackathon rules. Verified live public deployment URL: https://exercise-streams-manhattan-submitting.trycloudflare.com (verified via `scripts/deploy_smoke.py`, recorded in `docs/deployment-receipt.json` as `LIVE_DEPLOYED`). 100% reproducible local and containerized production execution is verified via Docker (`docker compose up --build`).

---

## 60-Second Quick Judge Tour

For a step-by-step evaluation guide, see our comprehensive [Judge Tour Guide](docs/JUDGE_TOUR.md):

1. **Header & Status:** Inspect `NMB-204` case metadata, temperature band (2.0°C–8.0°C), and truthful provider mode (`NOT_CONFIGURED` / `DEMO_FIXTURE`).
2. **Telemetry & Rail:** Review the 40-minute breach peaking at 10.5°C and correlate with the 10:18 UTC Newburgh Hub door-open event.
3. **Investigation Workflow:** Click **Investigate Excursion** to observe the 8-stage bounded state machine and verified regulatory guidance citations from CDC, FDA, and WHO.
4. **Adversarial Skeptic:** Review the 3 competing hypotheses and the Skeptic critique proving alternator bus voltage refutes reefer failure.
5. **Sensitivity & Quarantine:** In the Counterfactual Workbench, simulate a 5-minute door closure limit (reducing excursion duration from 40 min to 0 min) and inspect the printable Quarantine Review Packet.

---

## Known Limitations & Operational Boundaries

1. **Deterministic Offline Fixture Mode:** When credentials (`NEBIUS_TOKEN_FACTORY_KEY`, `TAVILY_API_KEY`) are not provided, ExcursionLens operates against frozen synthetic fixtures rather than live endpoints. It never claims `LIVE_TOKEN_FACTORY` or presents fabricated live receipts when operating in fixture mode.
2. **Single-Compartment Focus:** Canonical scenarios model single-compartment refrigerated transit. Multi-compartment vehicles carrying mixed temperature profiles (e.g. -20°C core and +4°C ambient) require discrete telemetry series per compartment.
3. **Decision-Support Boundary:** ExcursionLens outputs are investigative decision-support artifacts generated from sensor telemetry. In compliance with GxP regulations, the system cannot make an automatic release determination; physical goods remain segregated in `QUARANTINE_PENDING_QUALIFIED_REVIEW` until an authorized QA professional reviews and signs the packet.
4. **Structured Telemetry Ingestion:** The ingestion engine expects structured ISO-8601 timestamps and numerical sensor telemetry. Proprietary logger binary blobs require preprocessing into tabular or JSON format before ingestion.

---

## Project Documentation Index

- [Architecture Specification](docs/ARCHITECTURE.md)
- [Safety, Governance & Compliance Policy](docs/SAFETY.md)
- [Benchmark Evaluation & Validation Methodology](docs/EVALUATION.md)
- [Data Sources & Provenance Specification](docs/DATA_SOURCES.md)
- [Video Demonstration Script (<2:45)](docs/DEMO_SCRIPT.md)
- [Devpost Submission Copy](docs/DEVPOST_SUBMISSION.md)
- [Nebius Token Factory Developer Feedback](docs/TOKEN_FACTORY_FEEDBACK.md)
- [Submission Readiness Checklist](docs/SUBMISSION_CHECKLIST.md)

---

## License

ExcursionLens is licensed under the [Apache License, Version 2.0](LICENSE).
