# ExcursionLens Safety, Governance & Compliance Policy

## 1. Regulatory Context & Core Safety Invariant

Biopharmaceutical cold-chain logistics involves life-saving therapeutics (vaccines, blood products, biologics) whose potency and molecular integrity depend on strict temperature maintenance (typically 2.0°C to 8.0°C). Releasing spoiled biologics can lead to treatment failure or fatal adverse events.

### Mandatory Core Invariant: Anti-Auto-Release
**ExcursionLens is strictly an investigative and diagnostic aide. It is architecturally prohibited from making a final product release or destruction disposition.**

- The system output for any out-of-range thermal excursion is always:
  **`QUARANTINE_PENDING_QUALIFIED_REVIEW`**
- Physical inventory must remain segregated in temperature-controlled quarantine until authorized Quality Assurance (QA) personnel sign off.
- The software enforces this via a deterministic validator that scans all agent outputs and rejects any hypothesis, summary, or counterfactual claim containing auto-release or regulatory waiver language.

---

## 2. Adversarial Prompt Injection & Untrusted Input Defense

ExcursionLens ingests external data from IoT loggers, custody manifests, and live web research (Tavily). It treats all external strings as untrusted inputs.

### Protective Layers
1. **Strict URL and Domain Allowlisting:**
   - Tavily search queries are restricted to trusted public health domains: `cdc.gov`, `fda.gov`, `who.int`, and `gs1.org`.
   - All URLs returned must use the `https://` scheme. Any non-standard scheme (`javascript:`, `data:`, `file:`) or unauthorized domain is rejected immediately.
2. **Untrusted Data Framing:**
   - Content extracted from web pages or sensor logs is isolated inside explicit data blocks with strict content size caps (max 500 characters per snippet).
   - Prompts sent to NVIDIA Nemotron models instruct the model to treat external text strictly as factual reference data and to ignore any meta-instructions, jailbreak attempts, or commands embedded within retrieved snippets.
3. **Deterministic Grounding & Anti-Hallucination:**
   - Every generated claim must cite a known, pre-validated Observation ID (`OBS-*`) or Source ID (`SRC-*`).
   - Any assertion citing non-existent IDs is rejected by `apps/api/app/domain/validator.py`.

---

## 3. Graceful Degradation & Provider Failover

- If the Nebius Token Factory API key is absent, expired, or experiences rate limits, ExcursionLens degrades gracefully to **`DEMO_FIXTURE`** mode.
- The UI displays an unmissable amber banner: `● DEMO FIXTURE (Deterministic Local Analysis)`.
- It never fabricates provider success or returns simulated data disguised as live API outputs.

---

## 4. Operational Review Trail & Decision-Support Boundary

> **Important Boundary Notice:** ExcursionLens outputs are investigation-support evidence generated from synthetic or user-supplied telemetry. They do not determine product safety, potency, regulatory compliance or disposition. Follow organizational SOPs and obtain review from an authorized quality professional.

For quality documentation and investigation reconstruction:
- **Structured Review Export:** Every investigation run produces a cryptographically referenced JSON record containing timestamps, raw sensor data SHA-256 hashes, query digests, model IDs, receipts, and skeptic critique passes.
- **Formal Review Packet:** Generates a printable, standardized review packet (`review-packet.html`) with formal quality sign-off blocks, strict HTML escaping, and complete citation trees for authorized quality personnel.
