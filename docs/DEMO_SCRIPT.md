# ExcursionLens Video Demonstration Script

**Target Duration:** 2 minutes 30 seconds (Hard Cap: 2:45)  
**Tone:** Forensic, authoritative, calm, high signal-to-noise. No marketing hyperbole.

---

### Scene 1: The Problem & Shipment Case Overview (0:00 - 0:30)
- **Visual:** Browser showing `http://localhost:8000`. Fullscreen at 1920x1080.
- **Onscreen Action:** Cursor hovers over shipment ID `NMB-204`, product `Pentavalent Biologic Vaccine Lot 88B`, and the red alert badge `QUARANTINE PENDING QUALIFIED REVIEW`.
- **Spoken Narration:**
  > "Every year, billions of dollars in critical biopharmaceuticals and vaccines are lost to cold-chain temperature excursions during multimodal transit. In regulated operations under 21 CFR Part 11, you cannot simply guess whether a shipment is safe, nor can you trust a generative AI model that hallucinates approval. This is ExcursionLens: an evidence-first, bounded agent for cold-chain excursion forensics, powered by NVIDIA Nemotron on Nebius Token Factory and authoritative live search via Tavily."

---

### Scene 2: Deterministic Baseline & Event Alignment (0:30 - 0:55)
- **Visual:** Focus on the Temperature Telemetry Chart and the Custody/Operational Event Rail.
- **Onscreen Action:** Toggle "Show Accessible Table" to show raw timestamps, then scroll through the interactive chart showing the 42-minute breach window peaking at 10.5°C against the 2.0°C to 8.0°C compliant band. Point to the door-open event at 10:18 UTC.
- **Spoken Narration:**
  > "First, the foundation is 100% deterministic code. Before any AI call occurs, our Python domain engine parses the raw sensor time-series. For shipment NMB-204, it identifies a 42-minute breach above 8°C, peaking at 10.5°C with an area under the curve of 38.6 degree-minutes. Notice how the timeline aligns custody handshakes with vehicle IoT telemetry: exactly at 10:18 UTC, cargo door sensors trigger at Newburgh Transfer Hub Dock 3 during an unconditioned cross-dock transfer."

---

### Scene 3: Authoritative Guidance via Tavily (0:55 - 1:20)
- **Visual:** Click "Investigate Excursion". The Stage Tracker animates through stages 1 to 4.
- **Onscreen Action:** Expand the Sponsor Integration Proof Panel, highlighting the Tavily search queries and verified citations from `cdc.gov` and `who.int`.
- **Spoken Narration:**
  > "Clicking 'Investigate Excursion' triggers our bounded state machine. Stage 4 executes targeted Tavily searches restricted to strict public health domains—specifically the CDC Vaccine Storage Toolkit and WHO Good Distribution Practices. External content is strictly bounded and hashed to prevent prompt injection, providing ground-truth regulatory citations for thermal accumulation limits."

---

### Scene 4: Competing Hypotheses & Adversarial Skeptic Pass (1:20 - 1:50)
- **Visual:** Stages 5 and 6 complete. The Hypothesis Board reveals 3 competing hypotheses; the Adversarial Skeptic Panel updates.
- **Onscreen Action:** Cursor points to Hypothesis 1 (Transfer Staging Heat Infiltration) with high confidence, then to Hypothesis 2 (Reefer Power Failure). Hover over the Skeptic Critique showing how reefer bus voltage (12.8V-13.1V) directly refutes power loss. Click on evidence badge `OBS-EXCURSION-01` to show the Evidence Drawer.
- **Spoken Narration:**
  > "In Stages 5 and 6, NVIDIA Nemotron-70B synthesizes three competing causal hypotheses. Crucially, ExcursionLens runs an adversarial skeptic pass. While an ordinary LLM might speculate that the vehicle's refrigeration unit failed, our skeptic pass cross-checks the reefer alternator telemetry, which recorded steady 12.8 volts, directly falsifying the power loss theory. Every claim is validated against explicit observation IDs."

---

### Scene 5: Counterfactual Workbench & Review Packet (1:50 - 2:20)
- **Visual:** Counterfactual Workbench and Review Packet Modal.
- **Onscreen Action:** In the Counterfactual Workbench, select "Expedite Door Closing (5 min limit vs 24 min observed)" and click "Replay Counterfactual". The delta shows simulated excursion duration reduced from 42 min to 0.0 min. Then click "Review Packet" to display the full printable GMP packet with cryptographic hashes.
- **Spoken Narration:**
  > "To drive preventive corrective actions (CAPA), our Counterfactual Workbench allows QA engineers to replay interventions. Here, enforcing a 5-minute door closing rule prevents the thermal breach entirely. Finally, we generate an immutable Quality Review Packet, complete with evidence hashes, model signatures, and an unbending quarantine boundary. Physical stock remains safely segregated until human QA signs off."

---

### Scene 6: Conclusion & Submission Handoff (2:20 - 2:30)
- **Visual:** Return to main header showing clean state, provider receipts, and version tag.
- **Spoken Narration:**
  > "ExcursionLens bridges physical IoT reality, authoritative regulatory guidance, and NVIDIA Nemotron reasoning on Nebius Token Factory—transforming cold-chain compliance into an auditable, evidence-driven science. Thank you."
