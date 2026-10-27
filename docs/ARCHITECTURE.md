# ExcursionLens System Architecture

ExcursionLens is an evidence-first operational agent for investigating cold-chain biopharmaceutical temperature breaches. It bridges physical Internet-of-Things (IoT) sensor telemetry, multimodal custody events, authoritative regulatory research via Tavily, and deep causal reasoning using NVIDIA Nemotron models hosted on Nebius Token Factory.

```
                              EXCURSIONLENS ARCHITECTURE

   ┌────────────────────────────────────────────────────────────────────────┐
   │                       BROWSER CLIENT (React / TS)                       │
   │  - Timeline & Event Rail    - Hypothesis Board    - Skeptic Critique    │
   │  - Counterfactual Workbench - Evidence Inspector  - Human Review Packet │
   └───────────────────────────────────┬────────────────────────────────────┘
                                       │ HTTP / Server-Sent Events (SSE)
   ┌───────────────────────────────────▼────────────────────────────────────┐
   │                         FASTAPI BACKEND RUNTIME                         │
   │                                                                        │
   │   ┌────────────────────────────────────────────────────────────────┐   │
   │   │             STAGE 1 - 3: DETERMINISTIC CORE                    │   │
   │   │  • Schema Validation (Pydantic v2 strict models)               │   │
   │   │  • Telemetry Normalization & Rate-of-Change Analysis          │   │
   │   │  • Thermal Window, AUC, Peak, & Duration Detection Engine      │   │
   │   └───────────────────────────────┬────────────────────────────────┘   │
   │                                   │                                    │
   │   ┌───────────────────────────────▼────────────────────────────────┐   │
   │   │             STAGE 4: TAVILY AUTHORITATIVE RESEARCH             │   │
   │   │  • Strict Allowlist Enforcement (cdc.gov, fda.gov, who.int)    │   │
   │   │  • Query Digesting, Content Hashing, & Snippet Truncation      │   │
   │   └───────────────────────────────┬────────────────────────────────┘   │
   │                                   │                                    │
   │   ┌───────────────────────────────▼────────────────────────────────┐   │
   │   │             STAGE 5 - 6: NEBIUS TOKEN FACTORY                  │   │
   │   │  • NVIDIA Nemotron-70B Structured Hypothesis Generation       │   │
   │   │  • Adversarial Skeptic Pass (Contradiction & Falsification)   │   │
   │   └───────────────────────────────┬────────────────────────────────┘   │
   │                                   │                                    │
   │   ┌───────────────────────────────▼────────────────────────────────┐   │
   │   │             STAGE 7 - 8: CLAIMS VALIDATOR & REPORT             │   │
   │   │  • Deterministic Citation & Evidence ID Grounding              │   │
   │   │  • Anti-Auto-Release Invariant Enforcement                     │   │
   │   │  • Human Review Packet & JSON Audit Trail Generator            │   │
   │   └────────────────────────────────────────────────────────────────┘   │
   └────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Architectural Philosophy: Deterministic Core + Bounded AI

Cold-chain operations in life-sciences distribution strictly forbid ungrounded generative speculation in release decisions. ExcursionLens implements a hybrid architecture:

1. **Deterministic Sensory Layer (Python / NumPy / Pydantic):**
   - Telemetry parsing, time-delta calculations, gap detection, sensor drift, AUC (area under the curve above threshold), and threshold breach timings are 100% deterministic code.
   - Zero LLM tokens are involved in calculating whether a shipment breached 8.0°C or how long the door was open.

2. **Bounded Synthetic Agent (Nebius Token Factory + NVIDIA Nemotron):**
   - LLMs are invoked exclusively to form *competing hypotheses* regarding root causes (e.g., ambient staging heat vs. auxiliary compressor power failure vs. surface logger displacement).
   - An adversarial skeptic pass actively challenges these hypotheses against recorded custody and reefer telemetry.

3. **Strict Citation Validator:**
   - Every generated claim must cite explicit observations (`OBS-*`) or authoritative source IDs (`SRC-*`).
   - Any hallucinated ID or speculative claim without evidence is stripped or flagged by the deterministic validator.
   - The system strictly enforces the **Anti-Auto-Release Invariant**: it is architecturally prohibited from making a final release disposition. All outputs conclude in `QUARANTINE_PENDING_QUALIFIED_REVIEW` with an actionable human-review packet.

---

## 2. Component Directory Structure

```
nebius-nvidia-excursionlens/
├── apps/
│   ├── api/                     # Python 3.11+ FastAPI Service
│   │   ├── app/
│   │   │   ├── domain/          # Deterministic models, detector, validator, counterfactual
│   │   │   ├── providers/       # Nebius Token Factory & Tavily clients
│   │   │   ├── agent/           # 8-stage SSE state machine
│   │   │   ├── reports/         # Review packet & audit report generators
│   │   │   ├── config.py        # Environment & model settings
│   │   │   └── main.py          # FastAPI application & SPA static mount
│   │   └── tests/               # Pytest unit & integration suite
│   └── web/                     # React 18 + TypeScript + Vite SPA
│       ├── src/
│       │   ├── components/      # UI components (Timeline, Rail, Hypotheses, etc.)
│       │   ├── types.ts         # TypeScript domain contracts
│       │   └── index.css        # Minimalist forensic palette design tokens
│       └── dist/                # Production build bundled with FastAPI
├── benchmark/                   # 12 frozen synthetic benchmark scenarios
├── packages/fixtures/           # Canonical NMB-204 case fixture
├── docs/                        # Architecture, safety, evaluation, & submission assets
├── scripts/                     # Preflight, verification, live smoke, & security scripts
└── tests/e2e/                   # Playwright E2E & Axe accessibility tests
```

---

## 3. Data Flow & Stage State Machine

The investigation executes through eight discrete, traceable stages streamed over Server-Sent Events (SSE):

1. `VALIDATE_SCHEMA`: Validates custody records, temperature readings, and equipment metadata against Pydantic schemas.
2. `NORMALIZE_SERIES`: Computes rate of temperature rise, detects reading intervals, and flags sensor anomalies.
3. `DETECT_EXCURSION`: Identifies contiguous breach windows above 8.0°C (or below 2.0°C), calculates AUC and peak breach temperatures.
4. `TAVILY_GUIDANCE`: Queries authoritative guidelines (`cdc.gov`, `fda.gov`, `who.int`) using deterministic structured queries.
5. `NEMOTRON_HYPOTHESES`: Synthesizes 3 competing hypotheses (e.g. ambient heat infiltration, power loss, probe detachment) using NVIDIA Nemotron via Nebius Token Factory.
6. `ADVERSARIAL_SKEPTIC`: Evaluates counter-evidence (e.g., verifying vehicle bus voltage directly refutes auxiliary power failure).
7. `VALIDATE_CITATIONS`: Validates all factual citations against known observation and source IDs.
8. `QUALITY_REVIEW_PACKET`: Compiles the human review packet, sensitivity replay options, and structured review export.

---

## 4. Hardware & Deployment Efficiency

- **Container Footprint:** Single unified lightweight container running FastAPI + bundled React static bundle.
- **Inference Runtime:** OpenAI-compatible API client targeting Nebius Token Factory endpoints (`https://api.tokenfactory.nebius.com/v1`).
- **Cold-Start Latency:** < 500ms on commodity cloud runtimes.
