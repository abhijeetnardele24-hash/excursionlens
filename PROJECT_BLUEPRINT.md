# ExcursionLens — Project Blueprint

> **Single source of truth** for the Nebius x NVIDIA Global AI Hackathon build. If implementation and this document disagree, either restore the implementation to this blueprint or update this file with the reason and evidence for the decision.

## 1. Executive decision

**Project:** ExcursionLens  
**Tagline:** From a temperature alert to an evidence-backed investigation.  
**Primary track:** Best Apps and Agents  
**Bonus target:** Best Use of Tavily  
**Submission deadline:** October 30, 2026, 10:00 a.m. PDT (October 30, 2026, 10:30 p.m. IST)  
**Build posture:** New, standalone repository; no reused hackathon code or claims unless explicitly disclosed.

ExcursionLens is a human-in-the-loop investigation agent for cold-chain temperature excursions. It combines a shipment manifest, time-series sensor readings, custody events, and live authoritative guidance to reconstruct what happened, compare competing causal hypotheses, identify missing evidence, and produce a review packet for a quality professional.

The product does **not** decide that a vaccine, medicine, or food is safe, release inventory, or provide legal or medical advice. It recommends a review posture such as **quarantine pending qualified review**, makes uncertainty visible, and points the reviewer to the manufacturer or responsible authority.

### The one sentence judges should remember

> A temperature alarm tells you that something went wrong; ExcursionLens shows what the evidence supports, what it contradicts, what remains unknown, and what a human should verify next.

### Why this is the strongest realistic direction

- It avoids the hackathon's crowded coding-agent, generic assistant, and software-incident-response patterns.
- It solves a specific operational problem with credible public guidance and a visually demonstrable workflow.
- NVIDIA Nemotron is not decorative: it performs structured multi-source hypothesis synthesis, critique, and counterfactual planning that deterministic threshold code alone cannot do.
- Nebius Token Factory is used at runtime, with model discovery, inference receipts, bounded retries, and explicit failure states.
- Tavily is used at runtime to retrieve current, authoritative guidance and qualifies the project for the bonus award.
- Deterministic analysis remains responsible for temperature calculations; the model cannot invent or alter sensor facts.
- A polished two-minute demonstration can reveal the whole value chain: alert → evidence → hypotheses → challenge → next actions → export.

No concept can guarantee a win. This concept maximizes **differentiation, sponsor fit, judge comprehension, build feasibility, and proof quality** under the remaining deadline.

---

## 2. Official hackathon requirements

### 2.1 Objective and baseline eligibility gate

The hackathon asks builders to create a working AI system on open infrastructure. A valid submission must:

- run on **Nebius Token Factory or Nebius AI Cloud**;
- use at least one **NVIDIA open-source model**;
- fit one of the four tracks;
- make a genuine, non-superficial use of the required technologies.

For this project, “runs on Nebius” is satisfied by real runtime inference calls from the backend to an NVIDIA Nemotron model through Nebius Token Factory. Calling the same model through another provider would not satisfy this requirement.

### 2.2 Selected track

**Best Apps and Agents** is the correct track because ExcursionLens is a useful multi-step agentic application. The official guidance says that a single API call is only a starting point and an end-to-end workflow chaining tools is more distinctive.

Do not submit the project to Physical AI merely because sensor data is involved. There is no physical device in the MVP. Do not submit it as Personal AI or Coding and Agentic Engineering.

### 2.3 Submission deliverables

The final entry must include:

1. A working project using an NVIDIA open-source model on Nebius Token Factory or AI Cloud.
2. The **Best Apps and Agents** category selection.
3. A clear project description explaining what was built, why, and how it works.
4. A public, working demo URL, free and unrestricted through the judging period.
5. A **publicly visible YouTube video under three minutes** showing the functioning product and the Nebius/NVIDIA integration. “Unlisted” is not the rule-compliant default; use Public.
6. A public GitHub, GitLab, or Bitbucket repository containing all source code, assets, setup instructions, and an open-source license visible at repository top level.
7. A strong README explaining setup, NVIDIA Nemotron usage, Token Factory usage, architecture, evidence boundaries, demo flow, tests, and limitations.
8. Honest feedback on Nebius Token Factory, Nebius AI Cloud if used, and NVIDIA tools/models.
9. A prior-work disclosure if any part predates the submission period.
10. A functional runtime Tavily API call to qualify for Best Use of Tavily.

Judges may evaluate only the text, screenshots, and video, so those assets must communicate the project without requiring a local setup.

### 2.4 Judging criteria and response strategy

The four Stage Two criteria are equally weighted. Technological Implementation is the first tie-breaker.

| Criterion | What judges ask | ExcursionLens response | Evidence to show |
|---|---|---|---|
| Technological Implementation | Is it well built, and are Nebius/NVIDIA essential? | Real Token Factory calls; key-scoped model discovery; structured outputs; deterministic sensor engine; Tavily research tool; critic loop; provenance receipts; bounded agent execution | Live run, `/api/meta`, provider receipts, architecture diagram, contract tests, benchmark results |
| Design | Is it a coherent product rather than a technical toy? | A focused “investigation room” built around one case; clear separation of observed facts, inferences, contradictions, unknowns, and human actions | Responsive UI, strong empty/loading/error states, accessible interaction, downloadable review packet |
| Potential Impact | Is the audience and problem credible? | Small distributors, clinics, pharmacies, food operations, and QA teams need to document excursions and decide what to investigate next | CDC/FDA/WHO/GS1 grounding, realistic synthetic scenarios, time-to-review benchmark, explicit deployment path |
| Quality of Idea | Is the use of AI creative and problem-aware? | Not another monitoring dashboard: it begins after the alert, reconstructs the causal story, attacks its own hypotheses, and identifies the next discriminating evidence | Hypothesis board, contradiction matrix, counterfactual replay, ablation showing what each component adds |

### 2.5 Prize strategy

- Primary target: overall placement through a balanced score across all four criteria.
- Track target: Best Apps and Agents track award.
- Bonus target: Best Use of Tavily through a visible, functional runtime search call.
- Feedback target: provide concrete product feedback, not generic praise.
- Do not claim a City Winner Award unless the entrant actually attended an eligible in-person event.

---

## 3. Research synthesis

### 3.1 The real operational gap

Cold-chain platforms are good at monitoring, alerting, mapping, and preserving temperature records. Products such as Controlant and Sensitech already provide mature visibility, alerting, device integration, and audit functions. A generic “AI cold-chain dashboard” would therefore be weak and unoriginal.

The sharper gap is **post-alert investigation**:

- Which interval was actually out of range, and for how long?
- Did a door-open event, loading delay, reefer failure, power loss, or sensor fault best explain the trace?
- Which facts support each hypothesis and which facts contradict it?
- Is the available evidence sufficient for a qualified reviewer, or should the shipment remain quarantined while additional evidence is requested?
- Which current authority or manufacturer guidance applies?
- What preventive control would have changed the outcome?

CDC guidance for vaccine temperature excursions emphasizes immediate notification, “do not use” segregation, documentation of date/time, min/max temperature, duration, inventory, equipment issues, corrective action, and contact with the immunization program or manufacturer. FDA stability guidance says excursion evaluation depends on product stability data and supply-chain context. GS1 EPCIS provides a standard vocabulary for supply-chain event data, including sensor information. These facts justify an investigation assistant, but they also establish a hard boundary: ExcursionLens must never substitute for a qualified disposition decision.

### 3.2 Existing-solution comparison

| Existing pattern | Strength | Unserved opportunity ExcursionLens targets |
|---|---|---|
| Real-time cold-chain monitoring | Detects threshold violations quickly | Reconstruct and explain the incident after detection |
| Map-and-alert dashboard | Shows where an excursion occurred | Compare competing causes using custody and equipment events |
| Rule-based excursion report | Consistent calculations and forms | Identify contradictions, missing evidence, and the next best question |
| Generic RAG chatbot | Can summarize guidance | Bind every claim to case evidence, distinguish facts from hypotheses, and refuse disposition |
| Enterprise quality platform | Rich integrations and validated workflows | Lightweight, open-source investigation layer for smaller organizations and pilots |

ExcursionLens is not positioned as a replacement for validated enterprise systems. It is an open reference implementation of an evidence-first investigation layer.

### 3.3 Concept comparison

Scores use a 1–5 scale. Feasibility is deadline-adjusted.

| Concept | Originality | Feasibility | Technical depth | Sponsor alignment | Usefulness | Demo impact | Saturation risk | Total / 35 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **ExcursionLens — cold-chain investigation agent** | 5 | 4 | 5 | 5 | 5 | 5 | 4 | **33** |
| PermitDiff — municipal permit change-impact agent | 4 | 3 | 4 | 5 | 4 | 3 | 4 | 27 |
| ConsentFlow — privacy purpose-drift simulator | 5 | 3 | 4 | 5 | 4 | 3 | 4 | 28 |
| Production incident remediation agent | 2 | 4 | 5 | 5 | 5 | 5 | 1 | 27 |
| Persistent personal assistant | 2 | 4 | 4 | 5 | 4 | 3 | 1 | 23 |

The incident-remediation concept is technically impressive but visibly saturated in the current gallery. ExcursionLens wins the selection because it preserves technical depth while moving into a less crowded, high-consequence workflow with a clear visual narrative.

### 3.4 Authoritative references

- Hackathon overview: https://nebiusglobalaihackathon.devpost.com/
- Official rules: https://nebiusglobalaihackathon.devpost.com/rules
- Resources and credits: https://nebiusglobalaihackathon.devpost.com/resources
- FAQ: https://nebiusglobalaihackathon.devpost.com/details/faqs
- Judging guidance: https://nebiusglobalaihackathon.devpost.com/updates/46204-here-s-how-judging-works
- Nebius Token Factory: https://dev.nebius.com/token-factory
- NVIDIA Nemotron cookbook on Token Factory: https://github.com/nebius/token-factory-cookbook/tree/main/models/nemotron
- Nebius Token Factory integration guidance: https://github.com/nebius/nebius-physical-ai/blob/main/docs/workbench/token-factory.md
- NVIDIA Nemotron reasoning guidance: https://docs.nvidia.com/rag/latest/enable-nemotron-thinking.html
- Tavily Search API: https://help.tavily.com/articles/4840311948-tavily-search-api
- CDC vaccine storage and handling: https://www.cdc.gov/vaccines/hcp/storage-handling/
- CDC excursion response flow: https://www.cdc.gov/vaccines/hcp/downloads/storage-handling-toolkit-resources.pdf
- FDA ICH Q1 stability guidance: https://www.fda.gov/media/187161/download
- GS1 EPCIS 2.0: https://www.gs1.org/standards/epcis
- WHO controlled temperature chain: https://www.who.int/teams/immunization-vaccines-and-biologicals/essential-programme-on-immunization/supply-chain/controlled-temperature-chain-%28ctc%29
- Controlant platform comparison: https://www.controlant.com/platform
- Sensitech SmartView comparison: https://www.sensitech.com/en/products/smartview-software/

---

## 4. Product definition

### 4.1 Problem statement

A temperature threshold alert is not a complete investigation. Small quality teams often need to reconcile sensor logs, custody events, route events, product constraints, and external guidance before they can decide what to verify and whom to contact. The evidence is fragmented, causal explanations compete, and generic AI summaries can blur observed facts with speculation.

### 4.2 Target users

Primary:

- quality coordinators at small vaccine or medicine distributors;
- clinic and pharmacy cold-chain coordinators;
- food safety and logistics teams handling temperature-sensitive shipments;
- third-party logistics operators preparing an incident package for a qualified reviewer.

Secondary:

- auditors reviewing how an incident was investigated;
- operations managers identifying preventive controls;
- researchers and trainers teaching cold-chain incident response.

### 4.3 Core use cases

1. Investigate a shipment whose temperature exceeded its configured range.
2. Distinguish a likely physical excursion from a likely sensor fault.
3. Build an evidence request list before contacting a manufacturer or responsible program.
4. Generate a concise, reviewable incident packet with traceable sources.
5. Rehearse a counterfactual preventive action on a synthetic incident.
6. Train staff with benchmark scenarios without exposing patient or customer data.

### 4.4 The product promise

For one shipment, ExcursionLens creates a bounded investigation that answers:

- **Observed:** What do the raw data and events directly show?
- **Inferred:** Which explanations are plausible, and why?
- **Challenged:** What contradicts each explanation?
- **Unknown:** Which missing evidence would change the assessment?
- **Next:** What should a qualified human verify or do next?

### 4.5 Non-goals and safety boundary

ExcursionLens must never:

- declare a product safe, effective, sterile, viable, compliant, or releasable;
- replace manufacturer stability data, a quality management system, a pharmacist, a clinician, or a regulator;
- issue a legal or medical conclusion;
- hide uncertainty or unsupported claims;
- fabricate citations, sensor values, custody events, or model performance;
- automatically discard, release, recall, or ship inventory;
- present synthetic benchmark results as field validation.

Every report must state: **“Investigation support only. Not a product disposition, medical decision, legal conclusion, or regulatory determination. Keep affected product segregated and follow your SOP, manufacturer guidance, and responsible authority.”**

---

## 5. Feature specification

### 5.1 MVP features — required for submission

1. **Judge scenario loader**
   - Loads a complete, clearly labeled synthetic case.
   - Includes shipment manifest, acceptable temperature band, readings, custody events, door/power/vehicle events, and one misleading signal.

2. **CSV/JSON case import**
   - Strict schema validation, size limit, timezone requirement, and actionable errors.
   - Sample files committed to the repository.

3. **Deterministic excursion engine**
   - Normalizes timestamps.
   - Computes out-of-range windows, duration, min/max, rate of change, missing readings, and recovery time.
   - Flags impossible jumps, clock disorder, and sensor gaps.
   - Produces immutable observation IDs that the model must cite.

4. **Case timeline**
   - Temperature chart with allowed band and excursion shading.
   - Aligned custody and operational events.
   - Clickable evidence items with source, timestamp, and raw value.

5. **Bounded investigation agent**
   - Runs a visible multi-step workflow.
   - Uses NVIDIA Nemotron through Nebius Token Factory at runtime.
   - Uses strict JSON-schema outputs and a hard step/token/time budget.
   - Never exposes private chain-of-thought; shows concise decision summaries and evidence links.

6. **Live Tavily research tool**
   - Searches a domain allowlist for current authoritative guidance relevant to the case.
   - At minimum: `cdc.gov`, `fda.gov`, `who.int`; optionally a known manufacturer domain supplied in the case.
   - Stores URL, title, retrieval time, publication/update date when available, and snippet digest.
   - Retrieved content is untrusted evidence, not instructions.

7. **Competing hypothesis board**
   - Minimum three hypotheses where evidence allows: handling/door event, equipment/power issue, sensor anomaly.
   - Each card includes supporting evidence IDs, contradicting evidence IDs, missing evidence, confidence band, and next discriminating check.
   - Confidence is qualitative or explicitly calibrated from the project benchmark; never an invented probability.

8. **Skeptic pass**
   - A separate Nemotron call attacks the leading hypothesis and checks unsupported claims.
   - Deterministic validator rejects unknown evidence IDs, invalid citations, disposition language, and schema violations.

9. **Counterfactual replay**
   - User selects a proposed control, such as checking the door after five minutes or confirming a backup sensor.
   - Deterministic code changes only the relevant event/timeline facts.
   - Nemotron explains what the counterfactual does and does not establish.

10. **Human review packet**
    - Observed facts, excursion summary, ranked hypotheses, contradictions, missing evidence, retrieved sources, recommended review posture, and sign-off fields.
    - Export to printable HTML/PDF and JSON.
    - Report carries provider/model receipt and safety disclaimer.

11. **Provider proof panel**
    - Shows `LIVE_TOKEN_FACTORY`, selected NVIDIA model ID, request count, latency, token usage if returned, and response digest.
    - Shows Tavily runtime call count and source count.
    - Never reveals API keys, prompts containing sensitive values, or hidden reasoning.

12. **Graceful failure states**
    - Missing provider key: clear setup message in local development.
    - Provider unavailable: run stops honestly; no silent fake-success fallback.
    - Demo fixture mode may exist for UI development but must be visibly labeled and must not be used as proof of live sponsor integration.

### 5.2 Wow-factor features — build only after MVP is verified

- **Evidence-gap radar:** ranks missing evidence by expected ability to distinguish the top two hypotheses.
- **Ablation switch:** replays the same case as deterministic-only, Nemotron-without-research, and full system; visually demonstrates what each layer contributes.
- **Guidance freshness badge:** identifies retrieval date and warns when a source has no detectable update date.
- **EPCIS-shaped export:** map shipment events into a small, documented EPCIS 2.0-compatible subset.
- **Narrative diff:** compare initial hypothesis with post-skeptic result so judges can see the agent correct itself.
- **Investigation replay:** animate each tool call and evidence addition on the timeline.

### 5.3 Explicitly cut for the deadline

- Real IoT hardware ingestion.
- Automatic product release or discard.
- Manufacturer portal automation.
- Multi-tenant accounts, billing, and enterprise RBAC.
- Full validated GxP/21 CFR Part 11 claims.
- Blockchain.
- Predictive shelf-life or degradation models.
- Real patient, clinical, or commercial shipment data.
- A general-purpose chatbot.
- Vector database unless a measured need emerges.

---

## 6. Canonical judge scenario

Use a synthetic shipment named **NMB-204**. All names, products, locations, and values are fictional and must be labeled synthetic.

### Scenario summary

- Product class: temperature-sensitive biologic training sample.
- Required storage band: 2°C–8°C.
- Route: regional distribution center → transfer hub → community clinic.
- Readings: every five minutes.
- Excursion: temperature crosses 8°C after a transfer-hub custody event and remains elevated for 42 minutes before recovery.
- Candidate causes:
  1. container left open during handoff;
  2. temporary reefer power interruption;
  3. logger displaced near a warm surface or malfunctioning.
- Conflicting evidence:
  - a door event supports handling exposure;
  - vehicle power telemetry remains nominal, contradicting a broad power-loss theory;
  - a backup logger stays lower but also shows delayed warming, weakening a pure sensor-fault explanation.
- Missing evidence: photo/seal check, logger placement, receiving inspection note, and verified product-specific stability guidance.

### Expected demo outcome

The system should not choose a final product disposition. It should conclude that the handling-exposure hypothesis is best supported, retain a sensor-placement alternative, reject or downgrade generalized power loss, recommend quarantine pending qualified review, and request the missing evidence plus manufacturer/program guidance.

---

## 7. User experience and visual direction

### 7.1 Core journey

1. User opens the landing/case workspace and sees the privacy and decision-boundary notice.
2. User clicks **Load synthetic case NMB-204**.
3. A case-readiness gate validates timestamps, thresholds, and required fields.
4. User clicks **Investigate excursion**.
5. The UI streams named stages: Normalize → Detect → Research → Hypothesize → Challenge → Validate → Package.
6. The timeline highlights the 42-minute excursion and aligned custody events.
7. The hypothesis board shows supporting and contradicting evidence.
8. The user opens the Tavily evidence drawer and a Token Factory receipt.
9. The user runs one counterfactual control.
10. The user exports a human-review packet.

### 7.2 Information architecture

- `/` — focused introduction, problem, sample case CTA, system boundary.
- `/cases/:id` — primary investigation workspace.
- `/cases/:id/report` — print-ready review packet.
- `/evaluation` — benchmark and ablation results, clearly labeled.
- `/about` — architecture, privacy, limitations, sponsor integrations.

### 7.3 Workspace layout

- Header: project name, case mode badge, provider state, reset.
- Summary strip: shipment ID, configured band, excursion duration, review posture.
- Main canvas: synchronized temperature timeline and event rail.
- Right investigation rail: active stage, hypotheses, contradictions, evidence gaps.
- Lower section: authoritative sources, counterfactual controls, review packet preview.
- Sticky footer: human-review boundary and export action.

### 7.4 Intentional visual system

Direction: **forensic operations notebook**, not a neon AI dashboard.

- Canvas: warm mineral `#F3F0E8`.
- Ink: `#17201E`.
- Muted text: `#5D625D`.
- Rules: `#C8C1B3`.
- Excursion/caution: burnt vermilion `#B5482D`.
- Supported evidence: deep green `#275E4B`.
- Unknown/needs evidence: ochre `#9A6A1F`.
- Interactive accent: slate blue `#365E7D`.
- Typography: system sans for UI; tabular numerals; one restrained serif display face only if bundled legally.
- No gradients, glassmorphism, generic robot imagery, excessive cards, stock clip art, or “AI sparkle” icons.
- Motion: timeline reveal, evidence-line draw, gentle stage progress, and a restrained hypothesis reorder transition.

### 7.5 Accessibility

- WCAG-oriented contrast; do not claim formal compliance without a full audit.
- Keyboard-accessible chart summaries and controls.
- Text equivalent for all chart content.
- Focus visibility, reduced-motion support, semantic headings, live-region stage updates.
- Test at 320, 390, 768, 1280, and 1920 px.

---

## 8. Technical architecture

### 8.1 Recommended stack

- Frontend: React + TypeScript + Vite.
- Styling: CSS Modules or a small token-based CSS system; avoid a generic component theme.
- Charts: lightweight SVG/D3 primitives or Recharts with an accessible text summary.
- Backend: Python 3.12 + FastAPI + Pydantic v2.
- HTTP client: `httpx`.
- Database: SQLite through SQLModel or SQLAlchemy for local case/run metadata; no vector database.
- Provider client: official OpenAI-compatible client pointed to Nebius Token Factory, or direct `httpx` calls if that gives clearer receipts.
- Search: Tavily Search API through its official SDK or direct HTTPS API.
- Testing: Pytest, Vitest/Testing Library, Playwright, Axe.
- Packaging: one Docker image; FastAPI serves the built frontend and API.
- Public deployment: one container on a reliable public host. The runtime Token Factory call is what satisfies the Nebius requirement; Nebius Serverless is optional only if credentials and time permit.
- CI: GitHub Actions with typecheck, lint, unit tests, build, secret scan, and browser smoke tests.

### 8.2 System diagram

```text
Browser
  ├─ case import / sample scenario
  ├─ accessible timeline + hypothesis board
  └─ report export
        │ HTTPS/SSE
        ▼
FastAPI application
  ├─ Case Validator
  ├─ Deterministic Excursion Engine
  ├─ Bounded Investigation Orchestrator
  │    ├─ Tavily Research Tool ──► authoritative public sources
  │    ├─ Nemotron Investigator ─► Nebius Token Factory
  │    ├─ Nemotron Skeptic ──────► Nebius Token Factory
  │    └─ Evidence/Claims Validator
  ├─ Counterfactual Engine
  ├─ Report/Receipt Generator
  └─ SQLite run ledger (non-sensitive metadata)
```

### 8.3 Why not a heavy agent framework

Implement the orchestration as an explicit typed state machine. This makes every step, budget, transition, and failure inspectable. A framework may be added only if it reduces code and remains transparent; do not bury the core workflow in opaque abstractions.

### 8.4 Agent state machine

```text
CREATED
  → VALIDATING
  → NORMALIZING
  → EXCURSION_DETECTED
  → RESEARCHING
  → HYPOTHESES_DRAFTED
  → SKEPTIC_REVIEWED
  → CLAIMS_VALIDATED
  → HUMAN_REVIEW_READY

Any stage → FAILED_TRUTHFULLY
```

Each transition writes a compact event with timestamp, input/output digest, tool name, provider/model identity, latency, status, and error category. Do not log secrets or hidden reasoning.

### 8.5 Model strategy

Model availability is key-scoped and changes. Do not assume a model ID merely because it appears in documentation.

At startup or in a preflight command:

1. Call the Token Factory model catalog endpoint.
2. Filter for NVIDIA/Nemotron models available to the supplied key.
3. Choose configured IDs only if present.
4. Expose the selected canonical model IDs in `/api/meta`.
5. Fail with a clear setup error if no eligible NVIDIA model is available.

Configuration:

- `NEBIUS_TOKEN_FACTORY_KEY`
- `NEBIUS_TOKEN_FACTORY_BASE_URL=https://api.tokenfactory.nebius.com/v1/`
- `NVIDIA_FAST_MODEL_ID`
- `NVIDIA_DEEP_MODEL_ID`
- `TAVILY_API_KEY`
- `APP_MODE=live|fixture`

Preferred routing, subject to live catalog verification:

- Fast extraction/format repair: Nemotron 3.5 Lightning or another available fast NVIDIA Nemotron model.
- Hypothesis synthesis and skeptic pass: Nemotron 3 Super or Ultra if available and affordable.
- If only one eligible model is available, use it with two bounded prompt profiles and document that choice.

Never expose raw chain-of-thought. Request structured conclusions with evidence IDs, concise rationales, alternatives, and unknowns. If a model API offers hidden reasoning controls, keep private reasoning filtered from user-facing content and logs.

### 8.6 Tool contracts

#### `analyze_sensor_series`

Input: normalized readings, allowed range, sampling interval.  
Output: observation IDs, excursion windows, min/max, duration, gap flags, jump flags, recovery statistics.

#### `search_authoritative_guidance`

Input: case product class, excursion type, source allowlist.  
Output: source records with URL, title, domain, date, retrieval time, snippet, content digest.

#### `draft_hypotheses`

Input: observations, custody events, source records.  
Output: 2–4 hypotheses with support IDs, contradiction IDs, unknowns, and discriminating checks.

#### `challenge_hypotheses`

Input: hypotheses and complete evidence index.  
Output: unsupported claims, alternative explanations, downgraded claims, and missing tests.

#### `validate_claims`

Deterministic. Rejects:

- unknown observation/source IDs;
- URLs not returned by Tavily;
- invented numeric readings or durations;
- unsupported certainty;
- safety, release, compliance, or medical claims;
- malformed JSON;
- more than configured tool-call/token/time budgets.

#### `simulate_counterfactual`

Input: original case and one allowlisted intervention.  
Output: modified timeline, unchanged facts, changed observations, and explicit limits.

### 8.7 API surface

- `GET /api/health` — liveness only.
- `GET /api/meta` — commit, build time, mode, selected canonical model IDs, provider readiness; no secrets.
- `GET /api/models/capabilities` — redacted capability probe result.
- `POST /api/cases/validate` — parse and validate input.
- `POST /api/cases` — create case.
- `GET /api/cases/{id}` — fetch case.
- `POST /api/cases/{id}/investigations` — start bounded run.
- `GET /api/investigations/{id}/events` — SSE stage events.
- `GET /api/investigations/{id}` — result and receipts.
- `POST /api/investigations/{id}/counterfactuals` — run allowlisted replay.
- `GET /api/investigations/{id}/report.json` — audit export.
- `GET /api/investigations/{id}/report` — print-ready HTML.

### 8.8 Data model

#### Case

- `id`, `title`, `synthetic`, `created_at`
- `shipment`, `product_profile`, `temperature_policy`
- `readings[]`, `custody_events[]`, `operational_events[]`
- `input_digest`, `schema_version`

#### Observation

- `id`, `kind`, `start_at`, `end_at`
- `numeric_values`, `unit`, `source_event_ids[]`
- `detector_version`

#### SourceRecord

- `id`, `url`, `title`, `domain`
- `published_or_updated_at`, `retrieved_at`
- `snippet`, `content_digest`, `query`

#### Hypothesis

- `id`, `label`, `summary`
- `supporting_evidence_ids[]`, `contradicting_evidence_ids[]`
- `unknowns[]`, `next_check`
- `confidence_band`, `status`

#### InvestigationRun

- `id`, `case_id`, `state`, `created_at`, `completed_at`
- `provider_mode`, `requested_model`, `served_model`
- `tool_events[]`, `hypotheses[]`, `review_posture`
- `request_digest`, `response_digest`, `usage`, `latency_ms`
- `validation_result`, `failure_reason`

#### Counterfactual

- `id`, `run_id`, `intervention_type`, `parameters`
- `changed_fact_ids[]`, `unchanged_fact_ids[]`, `result_summary`

### 8.9 Frontend component map

- `AppShell`
- `CaseLoader`
- `CaseReadinessGate`
- `ShipmentHeader`
- `TemperatureTimeline`
- `EventRail`
- `StageTracker`
- `ObservationInspector`
- `HypothesisBoard`
- `EvidenceMatrix`
- `SourceDrawer`
- `ProviderProofPanel`
- `CounterfactualWorkbench`
- `ReviewPostureCard`
- `ReportPreview`
- `ErrorBoundary`
- `ModeBadge`

### 8.10 Backend module map

- `app/api/` — routes and schemas.
- `app/domain/` — deterministic temperature, timeline, and claim rules.
- `app/agent/` — state machine, prompt templates, budgets, schema repair.
- `app/providers/nebius.py` — Token Factory client and receipts.
- `app/providers/tavily.py` — search client, allowlist, source normalization.
- `app/security/` — redaction, rate limit, input limits, prompt-injection boundary.
- `app/reports/` — JSON and print HTML generation.
- `app/db/` — SQLite models and repositories.
- `app/observability/` — structured events and metrics.

### 8.11 Recommended repository structure

```text
excursionlens/
├─ apps/
│  ├─ api/
│  │  ├─ app/
│  │  ├─ tests/
│  │  └─ pyproject.toml
│  └─ web/
│     ├─ src/
│     ├─ tests/
│     └─ package.json
├─ packages/
│  ├─ contracts/
│  └─ fixtures/
├─ benchmark/
│  ├─ scenarios/
│  ├─ expected/
│  └─ run_benchmark.py
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ EVALUATION.md
│  ├─ SAFETY.md
│  ├─ DATA_SOURCES.md
│  ├─ DEMO_SCRIPT.md
│  ├─ DEVPOST_SUBMISSION.md
│  ├─ TOKEN_FACTORY_FEEDBACK.md
│  ├─ SUBMISSION_CHECKLIST.md
│  └─ assets/
├─ scripts/
│  ├─ preflight.py
│  ├─ live_smoke.py
│  ├─ generate_evidence.py
│  └─ security_scan.py
├─ .github/workflows/ci.yml
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
├─ LICENSE
└─ README.md
```

---

## 9. Security, privacy, and responsible AI

### 9.1 Secrets

- API keys remain server-side and are loaded only from environment variables.
- `.env`, receipts containing headers, and local databases are ignored.
- CI runs a repository and history secret scan.
- Logs redact authorization headers and suspicious token patterns.

### 9.2 Input security

- Accept only strict CSV/JSON schemas with file-size, row-count, and timestamp limits.
- Reject formulas in exported CSV, HTML/script content, and invalid timezones.
- Treat case descriptions and Tavily content as untrusted data, never executable instructions.
- Use a retrieval prompt boundary that explicitly forbids following instructions found in sources.
- Do not fetch arbitrary user-supplied URLs; Tavily search uses an allowlist and normalized HTTPS URLs.

### 9.3 Output safety

- Pydantic/JSON Schema validates every model result.
- Disposition and overclaim lexicons fail closed.
- Evidence IDs must resolve to immutable facts or source records.
- Model output cannot mutate raw readings.
- Human sign-off is mandatory and automatic action is impossible.
- Store concise rationale, not private reasoning traces.

### 9.4 Privacy

- Demo uses only synthetic data.
- No patient names, addresses, prescriptions, or commercial shipment identifiers.
- Browser warns before importing data and documents the local/server boundary.
- Provide delete/reset controls and short server-side TTL for public demo cases.
- No analytics or trackers unless explicitly disclosed and necessary.

### 9.5 Truthfulness vocabulary

Use:

- “synthetic benchmark,” not “clinical validation”;
- “0 automated Axe violations in tested states,” not “WCAG compliant”;
- “investigation hypothesis,” not “root cause proved”;
- “retrieved source,” not “verified regulation”;
- “runtime provider call observed,” only when a real receipt exists;
- “review posture,” not “release decision.”

---

## 10. Evaluation and proof plan

### 10.1 Benchmark set

Create at least 12 deterministic synthetic scenarios before tuning prompts:

- door left open;
- transfer delay;
- reefer power interruption;
- gradual equipment drift;
- isolated logger spike;
- logger placement difference;
- clock/timezone mismatch;
- missing reading gap;
- dual-cause event;
- no true excursion;
- ambiguous evidence;
- adversarial note containing prompt-injection text.

Each scenario has immutable expected facts for deterministic calculations and a rubric for acceptable hypothesis structure. The benchmark must be versioned and its limitations stated.

### 10.2 Metrics

Deterministic:

- excursion-window precision/recall against labeled intervals;
- duration and min/max exactness;
- timestamp normalization correctness;
- invalid-input rejection rate.

Agentic:

- valid structured output rate;
- evidence-ID precision: cited IDs that exist;
- unsupported-claim rate;
- contradiction coverage;
- required-unknown coverage;
- source-domain allowlist compliance;
- tool-budget compliance;
- completed-run rate and latency.

Product:

- task completion across the canonical journey;
- keyboard completion;
- automated accessibility scan results for tested states;
- mobile overflow and chart-summary tests.

### 10.3 Ablations

Run and label three configurations on the same scenarios:

1. deterministic engine only;
2. deterministic engine + Nemotron, no Tavily;
3. full system with Nemotron investigator, Tavily, and skeptic pass.

Do not manufacture improvement. Publish failures and explain what each layer actually changes.

### 10.4 Provider evidence

A live-provider evidence artifact should include:

- commit SHA;
- timestamp;
- Token Factory base hostname;
- requested and served canonical NVIDIA model ID;
- HTTP success status;
- latency and token usage if returned;
- request and response digests;
- Tavily call status, query digest, and returned source domains;
- no API keys, full prompts, hidden reasoning, or confidential content.

CI without secrets may skip live-provider tests, but a skipped test is not proof. Before submission, run a separate required live smoke command and commit only the redacted evidence artifact.

---

## 11. Implementation plan in verified vertical slices

### Phase 0 — preflight and capability proof

1. Create a new repository and confirm no old remotes or copied history.
2. Add license, `.gitignore`, `.env.example`, and minimal README.
3. Claim/configure Token Factory credits and Tavily access.
4. Implement the Token Factory model catalog probe.
5. Make one real NVIDIA Nemotron inference call and one real Tavily search call.
6. Save a redacted receipt and stop if either integration cannot work.

**Exit gate:** real provider calls succeed; canonical model IDs are known; no secrets are committed.

### Phase 1 — deterministic case truth

1. Define schemas and sample NMB-204 fixture.
2. Build timestamp normalization and excursion calculations test-first.
3. Add validation, observation IDs, and edge-case tests.
4. Expose case validation and deterministic analysis APIs.

**Exit gate:** calculations pass targeted tests on all 12 synthetic cases.

### Phase 2 — first judge-visible vertical slice

1. Build the case workspace and accessible temperature/event timeline.
2. Load NMB-204.
3. Show observed excursion facts and raw evidence inspector.
4. Add responsive/error/loading states.

**Exit gate:** a judge can load the case and understand the incident without AI.

### Phase 3 — live evidence and agent loop

1. Add Tavily allowlisted search and normalized source records.
2. Add Nemotron structured hypothesis generation.
3. Add skeptic pass and deterministic claims validator.
4. Stream named stages to the UI.
5. Add provider proof panel and truthful failure states.

**Exit gate:** one real live run completes and every claim resolves to evidence.

### Phase 4 — action and explanation

1. Add missing-evidence ranking.
2. Add one counterfactual replay.
3. Add report JSON/print export and mandatory disclaimer.
4. Add ablation display if time remains.

**Exit gate:** full canonical journey works end-to-end.

### Phase 5 — hardening

1. Unit, integration, contract, security, and provider mock tests.
2. Playwright journey at five viewport widths.
3. Axe scan in empty, loading, completed, and failed states.
4. Prompt-injection and invalid-citation tests.
5. Secret/history scan, dependency audit, production build, Docker smoke.

**Exit gate:** all required gates have fresh machine-readable outputs.

### Phase 6 — submission package

1. Deploy public working demo and verify from a private browser.
2. Produce architecture SVG and PNG.
3. Capture five real screenshots.
4. Finalize README and Devpost copy.
5. Record one public YouTube video under three minutes.
6. Verify repository public visibility, license, setup, demo, and feedback.

**Exit gate:** every item in Section 15 is checked with a real URL or artifact.

---

## 12. Demo strategy

### 12.1 Demo goal

In under 2:45, prove that ExcursionLens is a real, useful, multi-step agent whose conclusions are bounded by evidence and whose sponsor integrations are live.

### 12.2 Timed flow

| Time | Visual | Narration purpose |
|---|---|---|
| 0:00–0:15 | Temperature alert and fragmented evidence | State the problem: an alarm is not an investigation |
| 0:15–0:30 | Load synthetic NMB-204 | Establish realistic input and safety boundary |
| 0:30–0:55 | Timeline detects 42-minute excursion | Show deterministic facts first |
| 0:55–1:20 | Live stage tracker, Tavily source drawer, Token Factory badge | Prove real tool use and sponsor alignment |
| 1:20–1:50 | Hypothesis board with support/contradiction/unknowns | Reveal the unique kernel |
| 1:50–2:10 | Skeptic changes or downgrades a claim | Show self-correction, not a one-shot answer |
| 2:10–2:28 | Counterfactual replay | Demonstrate action-oriented reasoning |
| 2:28–2:43 | Review packet and disclaimer | Show practical output and human boundary |
| 2:43–2:45 | Tagline | Leave one memorable sentence |

### 12.3 Recording rules

- 1920×1080, 30 fps, one final video.
- Use only real application footage and real measured values.
- Public YouTube visibility, not Private and not Unlisted by default.
- No copyrighted music, unlicensed trademarks, fabricated UI, fabricated metrics, or visible keys/emails/private tabs.
- Show provider proof long enough to read, but never show secrets.
- Burn in concise captions and provide `.srt`.
- Cut waits longer than one second; if a live call takes time, use the real stage animation and state the measured latency.

---

## 13. Devpost description strategy

### Project name

**ExcursionLens**

### One-line pitch

An evidence-first agent that turns cold-chain temperature alerts into reviewable hypotheses, contradictions, and next actions.

### Story order

1. **Hook:** “An alarm says the temperature crossed a line. It does not explain why, whether the sensor is trustworthy, or what evidence a reviewer still needs.”
2. **Problem:** Cold-chain evidence is fragmented; generic summaries blur facts and inference.
3. **Solution:** deterministic sensor truth + Tavily authoritative research + Nemotron hypothesis/critic loop.
4. **Unique kernel:** every hypothesis must show support, contradiction, unknowns, and a discriminating next check.
5. **Working proof:** describe only the canonical live run and measured benchmark.
6. **Sponsor fit:** name the actual canonical NVIDIA model served by Token Factory and the exact Tavily runtime role.
7. **Safety:** human review, no product disposition, synthetic demo data.
8. **Learning and feedback:** specific integration friction, model-catalog behavior, latency/cost trade-offs, and desired improvements.

### Built With tags

Use only technologies actually present, likely:

`nebius-token-factory`, `nvidia-nemotron`, `tavily`, `python`, `fastapi`, `pydantic`, `react`, `typescript`, `vite`, `sqlite`, `docker`, `pytest`, `vitest`, `playwright`, `axe-core`

### Claims discipline

- Replace all planned numbers with actual measured outputs before submission.
- Never say “validated,” “compliant,” “production-ready,” or “clinically accurate” without appropriate evidence.
- State whether the public demo is live-provider or a cached replay.
- If live-provider service is unavailable during recording, fix it; do not present a fixture as live.

---

## 14. Required repository and media assets

### Repository documents

- `README.md` — polished overview, one-command quick start, architecture, provider setup, demo journey, evidence, limitations.
- `LICENSE` — Apache-2.0 or MIT.
- `docs/ARCHITECTURE.md`
- `docs/EVALUATION.md`
- `docs/SAFETY.md`
- `docs/DATA_SOURCES.md`
- `docs/DEMO_SCRIPT.md`
- `docs/DEVPOST_SUBMISSION.md`
- `docs/TOKEN_FACTORY_FEEDBACK.md`
- `docs/SUBMISSION_CHECKLIST.md`
- `docs/verification-results.json`

### Visual assets

- `docs/assets/architecture.svg`
- `docs/assets/architecture.png`
- `docs/assets/excursionlens-devpost-thumbnail.png` at 1280×720.
- `docs/assets/screenshots/01_case_overview.png`
- `docs/assets/screenshots/02_timeline_evidence.png`
- `docs/assets/screenshots/03_hypothesis_board.png`
- `docs/assets/screenshots/04_counterfactual.png`
- `docs/assets/screenshots/05_review_packet.png`

The thumbnail should show the timeline, three competing evidence paths, and the phrase **“Alert → Evidence → Human Review”**. It must not contain tiny unreadable feature lists or unsupported metrics.

---

## 15. Risks and fallback plan

| Risk | Early test | Fallback |
|---|---|---|
| Token Factory account/model unavailable | Phase 0 catalog and live inference | Contact Nebius Discord immediately; select another NVIDIA model returned by the catalog. Do not switch to another provider and claim eligibility |
| Deep model too slow or expensive | Measure one canonical run | Use one available NVIDIA model with separate fast/deep prompt profiles; cap steps and cache only the judge scenario's non-sensitive research sources |
| Tavily returns weak sources | Test allowlisted queries | Narrow query templates, show source quality and unknown state; never invent a citation |
| Model emits unsupported claims | Adversarial contract tests | Fail closed, retry once with validator feedback, then return structured failure |
| Public host cold-starts | Test from private browser repeatedly | Keep one-container architecture, add health warm-up, and record a real functioning run |
| Timeline UI consumes too much time | Build simple SVG first | Preserve accessible table and evidence board; animation is optional |
| Domain seems too regulated | Safety review | Position as investigation support/training, not disposition or compliance software |
| Benchmark appears self-serving | Freeze scenarios before prompt tuning | Publish schema, expected facts, failures, and limitations; distinguish deterministic and model metrics |
| Deadline pressure | Complete Phase 0 and first slice first | Cut ablation UI, EPCIS export, and advanced animation before cutting live integrations or the core evidence loop |

---

## 16. Final requirement coverage checklist

### Eligibility and sponsor fit

- [ ] New or properly disclosed project.
- [ ] Best Apps and Agents selected.
- [ ] Runtime call to Nebius Token Factory.
- [ ] At least one NVIDIA open-source model selected from the live key-scoped catalog.
- [ ] Model and provider use are essential and visible.
- [ ] Functional runtime Tavily API call.

### Working product

- [ ] Public demo URL loads without payment or special access.
- [ ] Canonical scenario completes from input to report.
- [ ] Deterministic calculations match expected values.
- [ ] Nemotron investigator and skeptic outputs pass schemas.
- [ ] All model claims resolve to evidence.
- [ ] Human-review boundary is visible in UI and export.
- [ ] Provider failure is truthful; no silent fixture success.

### Engineering evidence

- [ ] Typecheck and lint pass.
- [ ] Unit/integration tests pass.
- [ ] Live Token Factory smoke passes and writes a redacted receipt.
- [ ] Live Tavily smoke passes and writes a redacted receipt.
- [ ] Browser journey passes at required viewports.
- [ ] Automated accessibility scan results are reported precisely.
- [ ] Secret scan and dependency audit pass.
- [ ] Production build and Docker smoke pass.
- [ ] Benchmark and ablation results are fresh and reproducible.

### Repository

- [ ] Public repository.
- [ ] Visible open-source license.
- [ ] All source and required assets present.
- [ ] Best-in-class README with quick start and architecture.
- [ ] `.env.example` has names only, no real values.
- [ ] Sample synthetic data is clearly labeled.
- [ ] Clean working tree; commit SHA recorded.

### Submission

- [ ] Project description completed.
- [ ] Working demo URL completed.
- [ ] Public YouTube video is under three minutes.
- [ ] Video shows real product operation and sponsor integrations.
- [ ] Devpost gallery images and readable thumbnail uploaded.
- [ ] Built With tags are accurate.
- [ ] Token Factory/NVIDIA/Tavily feedback is specific and honest.
- [ ] Prior-work disclosure completed if applicable.
- [ ] No City Winner claim without actual attendance.
- [ ] All claims rechecked against machine evidence and live URLs.

---

## 17. Definition of done

ExcursionLens is done only when a judge can open the public app, load NMB-204, run a real bounded investigation using an available NVIDIA Nemotron model through Nebius Token Factory and a real Tavily search, inspect evidence-backed competing hypotheses and contradictions, run one counterfactual, export a human-review packet, verify the public repository and test evidence, and watch the entire value proposition in a public video shorter than three minutes.

Passing local tests alone is not submission readiness. A polished UI without real sponsor calls is not eligible. A live model call without evidence discipline is not competitive. The winning version must demonstrate all three: **real integration, coherent product design, and honest evidence.**
