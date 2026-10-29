# Devpost Submission — ExcursionLens

**Project Name:** ExcursionLens  
**Tagline:** Evidence-first cold-chain temperature excursion investigation agent using NVIDIA Nemotron on Nebius Token Factory.  
**Track:** Best Apps and Agents  
**Bonus Track:** None (Primary track only: Best Apps and Agents; Best Use of Tavily bonus track omitted pending live TAVILY_API_KEY receipt)  
**Repository:** https://github.com/abhijeetnardele24-hash/excursionlens  
**Public Video URL:** [PUBLIC_YOUTUBE_URL_PLACEHOLDER]  
**Deployment & Reproducibility:** Public deployment is REQUIRED by hackathon rules. Public cloud hosting is currently recorded as `BLOCKED` pending hosting credentials; 100% reproducible containerized non-root production execution is verified locally via `docker compose up --build`.  
**Current Posture:** `INTERNAL_COMPLETE_EXTERNAL_ACTION_REQUIRED` (All internal logic, deterministic physics, and quality gates 100% verified; live sponsor execution dispatchable via workflow upon configuring repository secrets).  

---

## Inspiration

According to the World Health Organization (WHO), up to 50% of vaccines are wasted globally each year in part due to cold-chain failures, temperature excursions, and logistical bottlenecks (*WHO Immunization Supply Chain Guidelines*). In life-sciences cold-chain distribution:
- Quality Assurance (QA) teams must manually correlate scattered manifests, isolated IoT data logger CSV files, and refrigerated van telemetry.
- Operators risk either releasing compromised medicines to patients or destroying millions of dollars of completely viable product because they cannot isolate whether a breach reached the thermal core of the vial or merely warmed the surface air during cross-dock pallet transfer.
- Generic LLM wrappers fail catastrophically here: they hallucinate approval, attempt unauthorized release decisions, and fabricate regulatory citations.

We built **ExcursionLens** to prove that agentic AI can be safely deployed in high-consequence operational environments through deterministic sensory anchoring, adversarial skeptic reasoning, and bounded web research.

---

## What It Does

ExcursionLens is an operational investigation copilot for pharmaceutical cold-chain logistics:
1. **Deterministic Sensor Ingestion & Alignment:** Automatically parses multimodal time-series telemetry (sampling frequency, sensor drift, ambient vs product temperatures, bus voltage) and aligns it with custody handshakes and cargo door sensors.
2. **Authoritative Guideline Retrieval via Tavily:** Integrated search architecture designed to query live public health guidance exclusively from trusted repositories (`cdc.gov`, `fda.gov`, `who.int`), extracting verifiable citations for vaccine stability. In offline/demo mode, the system falls back safely to pre-vetted verified fixture summaries.
3. **Competing Causal Reasoning via NVIDIA Nemotron:** Designed to leverage `nvidia/llama-3.1-nemotron-70b-instruct` on Nebius Token Factory to synthesize three competing causal hypotheses (e.g., cross-dock ambient staging exposure vs. reefer compressor power circuit failure vs. surface logger detachment).
4. **Adversarial Skeptic Pass:** The agent actively runs a counter-falsification pass to challenge its own hypotheses against cold physical evidence (e.g., verifying that nominal vehicle alternator voltage directly contradicts the auxiliary power failure hypothesis).
5. **Counterfactual Preventive Control Workbench:** Allows operations teams to simulate "what-if" interventions (e.g., enforcing a 5-minute door closing SLA or reading secondary thermal-mass core probes) to evaluate synthetic sensitivity replay without physical overclaims.
6. **Quality Review Packet:** Produces a standardized, print-ready quality review packet with SHA-256 evidence digests.

**Core Safety Invariant:** ExcursionLens strictly enforces an **Anti-Auto-Release Invariant**. The system is architecturally prohibited from making final release dispositions; all investigations terminate in `QUARANTINE_PENDING_QUALIFIED_REVIEW` with actionable human-review files.

> **Decision-Support Boundary Notice:** ExcursionLens outputs are investigation-support evidence generated from synthetic or user-supplied telemetry. They do not determine product safety, potency, regulatory compliance or disposition. Follow organizational SOPs and obtain review from an authorized quality professional.

---

## How We Built It

- **Inference & Reasoning:** Designed to use NVIDIA Nemotron (`nvidia/llama-3.1-nemotron-70b-instruct`) through Nebius Token Factory for structured JSON hypothesis generation and adversarial critique. Current committed execution evidence is fixture mode; live verification remains blocked pending credentials.
- **Authoritative Research:** Integrated Tavily Search API with automated tests verifying strict domain allowlisting (`cdc.gov`, `fda.gov`, `who.int`, `gs1.org`), snippet truncation, and content digest verification. In offline/demo mode, uses pre-vetted verified fixture summaries.
- **Backend Domain Engine:** Built with **Python 3.11+**, **FastAPI**, and **Pydantic v2**, executing 100% deterministic excursion window detection, area-under-the-curve (AUC) calculations, and claims validation.
- **Frontend Operational Canvas:** Developed with **React 18**, **TypeScript**, and **Vite**, adhering to a forensic operations aesthetic (minimalist palette: Canvas `#F3F0E8`, Ink `#17201E`, Excursion `#B5482D`, Supported `#275E4B`).
- **Comprehensive Quality Gates:** 12 frozen synthetic benchmark scenarios with 100% mathematical pass rate, canonical Pytest suite with 165 test cases (92.98% statement and 81.85% unrounded branch coverage under canonical pytest 9.2.0 on Python 3.11.17 with `--cov-fail-under=85`), and Playwright E2E + Axe accessibility scans (0 violations in tested states across 5 viewports). Evidence authority is bound to downloadable GitHub Actions CI artifacts (`verification-artifacts-<COMMIT_SHA>`) produced directly by the [ExcursionLens CI Workflow](https://github.com/abhijeetnardele24-hash/excursionlens/actions/workflows/ci.yml).

---

## Challenges We Overcame

1. **Eliminating Hallucinated Compliance Claims:** Generative models naturally tend to generate soothing language ("The excursion is minor; the shipment is safe for use"). We built a deterministic Claims Validator that parses every LLM hypothesis and programmatically strips prohibited release assertions, enforcing segregation boundaries.
2. **Aligning Asynchronous Multimodal Streams:** Reconciling 5-minute periodic IoT logger telemetry with irregular custody events (driver handoffs, dock arrival, gate scans) along a continuous UTC axis required custom temporal interpolation and event-offset mapping.
3. **Adversarial Contradiction Modeling:** Getting Nemotron to rigorously evaluate counter-evidence required crafting a dedicated Skeptic prompt that specifically penalizes hypotheses contradicting telemetry facts (such as vehicle alternator bus voltage).

---

## Accomplishments We're Proud Of

- **100% Deterministic Reproducibility:** Identical sensor logs yield mathematically identical breach windows and AUC metrics across every run.
- **Automated Accessibility Verification:** Evaluated with `@axe-core/playwright`, detecting zero violations in tested states across 5 distinct screen viewports (320px to 1920px). (Automated testing verifies targeted rules and does not claim full WCAG compliance).
- **Graceful Fixture Degradation & Truthful Fail-Closed State:** When run without API keys, ExcursionLens functions in an honest, transparent `DEMO_FIXTURE` mode with pre-validated synthetic receipts without ever fabricating provider success. Current posture is `INTERNAL_COMPLETE_EXTERNAL_ACTION_REQUIRED`.


---

## What We Learned

- High-consequence AI requires *bounded state machines*, not unconstrained agentic loops. Defining explicit stages (`VALIDATE_SCHEMA` → `DETECT_EXCURSION` → `TAVILY_GUIDANCE` → `NEMOTRON_HYPOTHESES` → `ADVERSARIAL_SKEPTIC` → `VALIDATE_CITATIONS` → `REVIEW_PACKET`) creates the transparency required for regulated industries.
- Dynamic catalog querying (`GET /v1/models`) with runtime NVIDIA model resolution ensures graceful fallback and architectural robustness across model naming evolutions.

---

## Developer Feedback for Nebius Token Factory & NVIDIA

1. **Model Catalog Filter Metadata:** The `GET /v1/models` endpoint returns basic model IDs, but adding explicit vendor (`nvidia`), architecture (`nemotron`), and supported capability tags (e.g., `json_schema`, `tool_use`) directly in the model object would eliminate heuristic name parsing.
2. **First-Token Latency on 70B Models:** Time-to-first-token (TTFT) on `nvidia/llama-3.1-nemotron-70b-instruct` showed occasional variance under cold start. Pre-warmed endpoints or dedicated low-latency token-factory tiers for operational pipelines would benefit real-time dispatchers.
3. **Native JSON Schema Enforcement:** While Nemotron followed JSON output prompts reliably at temperature 0.2, native `response_format={"type": "json_object"}` support directly backed by constrained sampling grammar would prevent occasional markdown code block wrapping. See our full feedback specification in [`docs/TOKEN_FACTORY_FEEDBACK.md`](TOKEN_FACTORY_FEEDBACK.md).

---

## What's Next for ExcursionLens

- Direct integration with GS1 Digital Link barcodes and active cellular logger APIs (Sensitech, TempTale, Emerson GO).
- Support for multi-compartment refrigerated shipping containers with heterogeneous temperature zones (-20°C mRNA vaccines and +4°C monoclonal antibodies on the same pallet).
- Automated Corrective and Preventive Action (CAPA) ticket generation directly into enterprise QMS software (Veeva Vault, TrackWise).

---

## Built With

- `python`
- `fastapi`
- `pydantic`
- `nebius-token-factory`
- `nvidia-nemotron`
- `tavily-api`
- `react`
- `typescript`
- `vite`
- `playwright`
- `axe-core`
- `docker`
