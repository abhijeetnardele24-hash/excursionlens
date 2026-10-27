# ExcursionLens Video Demonstration Script

**Target Duration:** 2 minutes 30 seconds (Hard Cap: 2:45, Official Limit: 3:00)  
**Tone:** Forensic, authoritative, calm, high signal-to-noise. No marketing hyperbole.  
*Designed to use NVIDIA Nemotron through Nebius Token Factory. Current committed execution evidence is fixture mode; live verification remains blocked pending credentials.*

---

## Public Video Requirements & Hackathon Constraints

> [!IMPORTANT]
> **Devpost Submission Video Rules:**
> - **Hosting:** Must be uploaded to YouTube or Vimeo and set to **Public** or **Unlisted** (do NOT set to Private).
> - **Duration:** Must be strictly **under 3 minutes** (our script is timed to 2:30 with a 2:45 safety buffer).
> - **Visual Standard:** Record in 1080p (1920×1080) at 60fps or 30fps. Must demonstrate the live working UI at `http://localhost:8000`.
> - **Narration:** Clear spoken voiceover highlighting the deterministic baseline, Tavily grounding, NVIDIA Nemotron reasoning on Nebius Token Factory, skeptic falsification, and human review packet.

---

## Master Shot List & Scene Storyboard

| Scene | Timecode | Visual / URL | Onscreen Action | Audio / Spoken Focus |
|:---:|:---:|:---|:---|:---|
| **01** | `0:00 - 0:30` | `http://localhost:8000` Header & Case Card | Hover NMB-204, Lot 88B, red quarantine badge | The $35B cold-chain blindspot; deterministic safety boundary |
| **02** | `0:30 - 0:55` | Temperature Chart & Event Rail | Toggle table, highlight 40-min breach, 10.5°C peak, 10:18 UTC door event | 100% deterministic code; correlation of IoT logger with dock door |
| **03** | `0:55 - 1:20` | Stage Tracker & Tavily Proof Panel | Click "Investigate Excursion", expand Tavily panel, show CDC/WHO sources | Authoritative public health retrieval; domain allowlisting |
| **04** | `1:20 - 1:50` | Hypothesis Board & Skeptic Panel | Show 3 competing hypotheses; hover skeptic critique of reefer voltage | NVIDIA Nemotron reasoning on Nebius; adversarial contradiction pass |
| **05** | `1:50 - 2:20` | Counterfactual Workbench & Modal | Select 5-min door limit, click replay (40min → 0min); open Review Packet | Sensitivity replay controls; printable review packet with SHA-256 digests |
| **06** | `2:20 - 2:30` | Summary Header & Footer | Show clean audit state, receipts, version tag | Closing summary: IoT reality + Tavily grounding + Nemotron reasoning |

---

### Scene 1: The Problem & Shipment Case Overview (0:00 - 0:30)
- **Visual:** Browser showing `http://localhost:8000`. Fullscreen at 1920x1080.
- **Onscreen Action:** Cursor hovers over shipment ID `NMB-204`, product `Pentavalent Biologic Vaccine Lot 88B`, and the red alert badge `QUARANTINE PENDING QUALIFIED REVIEW`.
- **Spoken Narration:**
  > "Every year, billions of dollars in critical biopharmaceuticals and vaccines are lost to cold-chain temperature excursions during multimodal transit. In high-consequence operations, you cannot simply guess whether a shipment is safe, nor can you trust an unconstrained AI model that hallucinates approval. This is ExcursionLens: an evidence-first, bounded agent for cold-chain excursion forensics, powered by NVIDIA Nemotron on Nebius Token Factory and authoritative live search via Tavily."

---

### Scene 2: Deterministic Baseline & Event Alignment (0:30 - 0:55)
- **Visual:** Focus on the Temperature Telemetry Chart and the Custody/Operational Event Rail.
- **Onscreen Action:** Toggle "Show Accessible Table" to show raw timestamps, then scroll through the interactive chart showing the 40-minute breach window peaking at 10.5°C against the 2.0°C to 8.0°C configured temperature band. Point to the door-open event at 10:18 UTC.
- **Spoken Narration:**
  > "First, the foundation is 100% deterministic code. Before any AI call occurs, our Python domain engine parses the raw sensor time-series. For shipment NMB-204, it identifies a 40-minute breach above 8°C, peaking at 10.5°C with an area under the curve of 50.5 degree-minutes. Notice how the timeline aligns custody handshakes with vehicle IoT telemetry: exactly at 10:18 UTC, cargo door sensors trigger at Newburgh Transfer Hub Dock 3 during an unconditioned cross-dock transfer."

---

### Scene 3: Authoritative Guidance via Tavily (0:55 - 1:20)
- **Visual:** Click "Investigate Excursion". The Stage Tracker animates through stages 1 to 4.
- **Onscreen Action:** Expand the Sponsor Integration Proof Panel, highlighting the Tavily search queries and verified citations from `cdc.gov` and `who.int`.
- **Spoken Narration:**
  > "Clicking 'Investigate Excursion' triggers our bounded state machine. Stage 4 executes targeted Tavily searches restricted to strict public health domains—specifically the CDC Vaccine Storage Toolkit and WHO Good Distribution Practices. External content is strictly bounded and hashed to prevent prompt injection, providing ground-truth reference citations for thermal accumulation limits."

---

### Scene 4: Competing Hypotheses & Adversarial Skeptic Pass (1:20 - 1:50)
- **Visual:** Stages 5 and 6 complete. The Hypothesis Board reveals 3 competing hypotheses; the Adversarial Skeptic Panel updates.
- **Onscreen Action:** Cursor points to Hypothesis 1 (Transfer Staging Heat Infiltration) with high confidence, then to Hypothesis 2 (Reefer Power Failure). Hover over the Skeptic Critique showing how reefer bus voltage (12.8V-13.1V) directly refutes power loss. Click on evidence badge `OBS-EXCURSION-01` to show the Evidence Drawer.
- **Spoken Narration:**
  > "In Stages 5 and 6, NVIDIA Nemotron-70B synthesizes three competing causal hypotheses. Crucially, ExcursionLens runs an adversarial skeptic pass. While an ordinary LLM might speculate that the vehicle's refrigeration unit failed, our skeptic pass cross-checks the reefer alternator telemetry, which recorded steady 12.8 volts, directly falsifying the power loss theory. Every claim is validated against explicit observation IDs."

---

### Scene 5: Counterfactual Workbench & Review Packet (1:50 - 2:20)
- **Visual:** Counterfactual Workbench and Review Packet Modal.
- **Onscreen Action:** In the Counterfactual Workbench, select "Expedite Door Closing (5 min limit vs 24 min observed)" and click "Replay Counterfactual". The delta shows simulated excursion duration reduced from 40.0 min to 0.0 min. Then click "Review Packet" to display the full printable quality packet with cryptographic hashes.
- **Spoken Narration:**
  > "To evaluate preventive sensitivity controls, our Counterfactual Workbench allows QA engineers to replay interventions. Here, enforcing a 5-minute door closing rule prevents the thermal breach entirely in simulation. Finally, we generate a formal Quality Review Packet, complete with evidence hashes, model signatures, and an unbending quarantine boundary. Physical stock remains safely segregated until human QA signs off."

---

### Scene 6: Conclusion & Submission Handoff (2:20 - 2:30)
- **Visual:** Return to main header showing clean state, provider receipts, and version tag.
- **Spoken Narration:**
  > "ExcursionLens bridges physical IoT reality, authoritative regulatory guidance, and NVIDIA Nemotron reasoning on Nebius Token Factory—transforming cold-chain compliance into an auditable, evidence-driven science. Thank you."
