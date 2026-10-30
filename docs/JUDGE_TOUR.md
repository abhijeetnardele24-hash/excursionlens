# ExcursionLens: 60-Second Guided Tour for Hackathon Judges

**Project:** ExcursionLens (Cold-Chain Temperature Excursion Forensics Agent)  
**Hackathon Track:** Nebius x NVIDIA Hackathon — *Best Apps and Agents* (Primary track; *Best Use of Tavily* bonus track omitted pending live credential receipt)  
**Quick Start:**
```bash
docker compose up --build
```
Open **`http://localhost:8000`** locally, or evaluate the verified temporary public demonstration tunnel at **`https://exercise-streams-manhattan-submitting.trycloudflare.com`**.

---

## Welcome Judges & Technical Reviewers

ExcursionLens is an evidence-first, bounded forensic operations agent designed to investigate biopharmaceutical cold-chain temperature breaches during multimodal logistics. It is architecturally engineered to use **NVIDIA Nemotron (`nvidia/llama-3.1-nemotron-70b-instruct`)** through **Nebius Token Factory** and authoritative web search through **Tavily**.

Follow this 5-stop walkthrough to evaluate the complete core journey in under 60 seconds:

---

### Stop 1: Shipment Header & Fail-Closed Posture
- **Location:** Top navigation bar and primary Case Summary Card.
- **What to Observe:**
  - Shipment ID **`NMB-204`**, carrying *Pentavalent Biologic Vaccine Lot 88B*, with a strict **2.0°C to 8.0°C** allowable thermal band.
  - Initial Quality Posture: **`QUARANTINE PENDING QUALIFIED REVIEW`** (Red alert badge).
  - Provider Status Pill: Displays **`NOT_CONFIGURED`** / **`DEMO_FIXTURE`** in the public checkout. ExcursionLens never fabricates live inference when API keys are absent; it operates fail-closed with cryptographically verified synthetic fixtures.

### Stop 2: Deterministic Baseline & Event Alignment
- **Location:** Temperature Telemetry Chart & Multimodal Event Rail.
- **What to Observe:**
  - **Zero LLM tokens** are used for temperature physics or breach detection.
  - The Python engine deterministically calculates an exact **40.0-minute excursion** above 8.0°C, reaching a peak temperature of **10.5°C** and an Area Under the Curve (AUC) of **50.5 degree-minutes**.
  - Toggle **"Show Accessible Table"** to inspect raw time-series data.
  - Compare the temperature spike with the custody rail: the breach correlates exactly with unconditioned cross-dock transfer and open bay doors at Newburgh Hub at **10:18 UTC**.

### Stop 3: 8-Stage Investigation State Machine & Guidance Grounding
- **Location:** Action Bar and Stage Tracker.
- **What to Observe:**
  - Click the primary action button: **`Investigate Excursion`**.
  - The investigation streams in real time across 8 discrete states (Schema Validation $\to$ Normalization $\to$ Detection $\to$ Guidance $\to$ Hypothesis $\to$ Skeptic $\to$ Citation Validation $\to$ Review Packet).
  - In Stage 4, click on the **Evidence Drawer** to view authoritative guidance citations from **CDC Vaccine Storage and Handling**, **FDA Q1A(R2)**, and **WHO Controlled Temperature Chain**.
  - Notice the truthful provenance labeling: fixture summaries are explicitly labeled *`Verified fixture summary — not a live quotation`* with verification dates and official source links, never masquerading as live external retrievals.

### Stop 4: Competing Hypotheses & Adversarial Skeptic Pass
- **Location:** Hypothesis Board and Adversarial Skeptic Panel.
- **What to Observe:**
  - Stage 5 generates three competing causal hypotheses for the excursion.
  - Stage 6 executes our **Adversarial Skeptic Pass**: the system specifically audits each hypothesis against physical telemetry contradictions.
  - Hover over the Skeptic Critique on Hypothesis 2 (*Refrigeration Compressor Power Loss*): the skeptic highlights that the vehicle alternator bus voltage remained steady at **12.8V–13.1V**, directly refuting electrical failure and identifying dock infiltration as the primary root cause.
  - The Claims Validator programmatically strips any unauthorized release determinations.

### Stop 5: Counterfactual Sensitivity Workbench & Quarantine Packet
- **Location:** Lower operational controls and Review Packet Modal.
- **What to Observe:**
  - In the **Counterfactual Workbench**, select the intervention: *Expedite Door Closing (5 min limit vs 24 min observed)*.
  - Click **Replay Counterfactual**: the simulated excursion duration drops from **40.0 min to 0.0 min**, demonstrating actionable CAPA (Corrective and Preventive Action) insights.
  - Click **Review Packet**: inspect the printable audit trail containing telemetry digests, observation hashes, model execution logs, and regulatory citations.
  - **Anti-Auto-Release Invariant:** ExcursionLens architecturally refuses to authorize product release; the disposition concludes strictly in *`QUARANTINE_PENDING_QUALIFIED_REVIEW`* requiring authorized human quality sign-off.

---

## Technical Verification Summary

ExcursionLens is independently verified through GitHub Actions CI on Ubuntu Linux:
- **165 of 165 Pytest test cases passing.**
- **92.98% Statement Coverage** (1,471 / 1,582 statements).
- **81.85% Unrounded Branch Coverage** (424 / 518 branches).
- **12 of 12 Synthetic Benchmark Scenarios passing** with 100% precision.
- **25 of 25 Playwright E2E and Axe accessibility viewport executions passing** (0 violations in tested states).
- **Hardened non-root runtime container** executing as UID 10001 (`appuser`).
- **Zero committed secrets or private credentials.**

