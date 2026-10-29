# ExcursionLens Video Demonstration Scripts

> **Implementation Status & Provider Reality Notice:**  
> ExcursionLens is implemented to use NVIDIA Nemotron (`nvidia/llama-3.1-nemotron-70b-instruct`) through Nebius Token Factory and authoritative live search via Tavily.  
> **Current committed repository evidence is fixture mode (`DEMO_FIXTURE`); live provider verification remains blocked pending real external credentials.**  
>
> Below are two complete, distinct script variants depending on whether external API credentials have been supplied.

---

# Variant 1: FIXTURE_MODE_DRAFT — DO NOT SUBMIT AS LIVE PROOF

> [!WARNING]
> **DRAFT SCRIPT ONLY — DO NOT SUBMIT AS LIVE EVIDENCE TO DEVPOST**  
> This script is calibrated for recording internal walkthroughs, local rehearsals, and architecture validation in fixture mode (`DEMO_FIXTURE` / `NOT_CONFIGURED`).  
> It states honestly to the viewer that external keys are absent in the public checkout, showcasing the full deterministic safety boundaries, counterfactual engine, and UI workflow without pretending live inference has occurred.

**Target Duration:** 2 minutes 30 seconds (Hard Cap: 2:45, Official Limit: 3:00)  
**Tone:** Forensic, transparent, methodical, engineering-rigorous.  
**Operating Mode:** Fixture Mode (`DEMO_FIXTURE`), `http://localhost:8000`

### Scene Storyboard (Fixture Mode Draft)

| Scene | Timecode | Visual / URL | Onscreen Action | Audio / Spoken Focus |
|:---:|:---:|:---|:---|:---|
| **01** | `0:00 - 0:30` | `http://localhost:8000` Header & Case Card | Show `NOT_CONFIGURED` badge, NMB-204 case card, red quarantine badge | The $35B cold-chain blindspot; fail-closed safety boundary; fixture baseline |
| **02** | `0:30 - 0:55` | Temperature Chart & Event Rail | Toggle accessible table, highlight 40-min breach, 10.5°C peak, 10:18 UTC door event | Deterministic Python engine; IoT logger correlation with dock door |
| **03** | `0:55 - 1:20` | Stage Tracker & Provider Panel | Click "Investigate Excursion", expand Provider panel, show cached CDC/WHO guidance | Bounded state machine; pre-vetted regulatory guidance fallback |
| **04** | `1:20 - 1:50` | Hypothesis Board & Skeptic Panel | Show 3 competing hypotheses; hover skeptic critique of reefer voltage | Nemotron-70B causal architecture; adversarial contradiction pass |
| **05** | `1:50 - 2:20` | Counterfactual Workbench & Modal | Select 5-min door limit, click replay (40min → 0min); open Review Packet | Sensitivity replay controls; printable review packet with SHA-256 digests |
| **06** | `2:20 - 2:30` | Header & Footer Audit State | Point out truthful provider status (`DEMO_FIXTURE`) and fail-closed posture | Summary: Deterministic reality + adversarial falsification + human review |

#### Scene 1: The Cold-Chain Problem & Fail-Closed Safety (0:00 - 0:30)
- **Visual:** Browser showing `http://localhost:8000`. Fullscreen at 1920x1080.
- **Onscreen Action:** Cursor points to shipment ID `NMB-204`, product `Pentavalent Biologic Vaccine Lot 88B`, the red alert badge `QUARANTINE PENDING QUALIFIED REVIEW`, and the header badge displaying `NOT_CONFIGURED`.
- **Spoken Narration:**
  > "Every year, billions of dollars in critical biopharmaceuticals and vaccines are compromised by cold-chain excursions during transit. In regulated life sciences, an unconstrained AI that hallucinates approval can lead to compromised medication reaching patients. This is ExcursionLens: an evidence-driven, bounded forensic system built to use NVIDIA Nemotron on Nebius Token Factory. Notice our header: in this public repository checkout without live keys, our runtime correctly reports NOT_CONFIGURED. The system operates fail-closed, using pre-vetted fixtures rather than faking live execution."

#### Scene 2: Deterministic Baseline & Sensor Alignment (0:30 - 0:55)
- **Visual:** Focus on the Temperature Telemetry Chart and the Custody/Operational Event Rail.
- **Onscreen Action:** Toggle "Show Accessible Table" to reveal raw time-series, then scroll through the interactive chart showing the 40-minute breach window peaking at 10.5°C against the 2.0°C to 8.0°C configured temperature band. Point to the door-open event at 10:18 UTC.
- **Spoken Narration:**
  > "Our foundation is 100% deterministic code. Before any model executes, the Python domain engine analyzes the raw IoT telemetry. For shipment NMB-204, it calculates an exact 40-minute breach above 8°C, peaking at 10.5°C with an area under the curve of 50.5 degree-minutes. When aligned with custody logs, the breach correlates precisely with an unconditioned cross-dock transfer and open bay doors at Newburgh Hub at 10:18 UTC."

#### Scene 3: Bounded Workflow & Guidance Fallback (0:55 - 1:20)
- **Visual:** Click "Investigate Excursion". The Stage Tracker steps through stages 1 to 4.
- **Onscreen Action:** Expand the Sponsor Integration Proof Panel, highlighting the retrieval state and verified guidance citations from CDC and WHO.
- **Spoken Narration:**
  > "Clicking 'Investigate Excursion' triggers our bounded state machine. In live production, Stage 4 queries Tavily across an allowlist of public health domains like CDC and WHO. In this fixture demonstration, the system falls back safely to pre-vetted, cryptographically digested regulatory guidance records, establishing the allowable thermal threshold without external network dependencies."

#### Scene 4: Competing Hypotheses & Adversarial Skeptic Pass (1:20 - 1:50)
- **Visual:** Stages 5 and 6 complete. The Hypothesis Board displays 3 competing hypotheses; the Adversarial Skeptic Panel updates.
- **Onscreen Action:** Cursor highlights Hypothesis 1 (Transfer Staging Infiltration) vs Hypothesis 2 (Reefer Compressor Failure). Hover over the Skeptic Critique showing how reefer bus voltage (12.8V-13.1V) refutes power failure. Click on observation badge `OBS-EXCURSION-01` to show the Evidence Drawer.
- **Spoken Narration:**
  > "Stages 5 and 6 execute our dual-pass causal engine, structured for NVIDIA Nemotron-70B on Nebius. First, generator synthesis produces three competing hypotheses. Next, an adversarial skeptic pass tests each hypothesis against telemetry. While a naive model might blame refrigeration failure, the skeptic identifies that the vehicle alternator bus remained stable at 12.8 volts, directly falsifying compressor power loss. Prohibited overclaims are trapped by strict regex validators."

#### Scene 5: Counterfactual Sensitivity Workbench & Review Packet (1:50 - 2:20)
- **Visual:** Counterfactual Workbench and Review Packet Modal.
- **Onscreen Action:** In the Counterfactual Workbench, select "Expedite Door Closing (5 min limit vs 24 min observed)" and click "Replay Counterfactual". The delta highlights simulated excursion duration reduced from 40.0 min to 0.0 min. Then click "Review Packet" to display the full printable quality packet.
- **Spoken Narration:**
  > "To assist quality engineers with corrective actions, our Counterfactual Workbench simulates operational interventions. Enforcing a 5-minute door closure threshold eliminates the excursion completely in simulation. Finally, ExcursionLens generates a signed Quality Review Packet containing observation digests, model receipts, and strict quarantine boundaries. The product remains quarantined until qualified human QA signs off."

#### Scene 6: Conclusion (2:20 - 2:30)
- **Visual:** Return to main header showing clean state and audit footer.
- **Spoken Narration:**
  > "ExcursionLens bridges physical IoT reality, rigorous regulatory guidance, and adversarial reasoning—turning cold-chain compliance into an auditable science. Thank you."

---

# Variant 2: LIVE_VERIFIED_FINAL — Usable Only After Successful Provider Receipts

> [!IMPORTANT]
> **PREREQUISITE FOR USING THIS SCRIPT:**  
> Use this script **only after** real external API credentials have been configured in your environment:
> 1. `NEBIUS_TOKEN_FACTORY_KEY` set to an active Nebius Token Factory token.
> 2. `TAVILY_API_KEY` set to an active Tavily Search API key.
> 3. `python scripts/live_smoke.py` has run and exited with code 0.
> 4. `docs/live-smoke-receipt.json` records `"status": "LIVE_VERIFIED"`, tested model `nvidia/llama-3.1-nemotron-70b-instruct`, live HTTP round-trip latency, and valid token usage digests.

**Target Duration:** 2 minutes 30 seconds (Hard Cap: 2:45, Official Limit: 3:00)  
**Tone:** Authoritative, high signal-to-noise, forensically verified.  
**Operating Mode:** Live Verified Mode (`LIVE_VERIFIED`), `http://localhost:8000`

### Scene Storyboard (Live Verified Final)

| Scene | Timecode | Visual / URL | Onscreen Action | Audio / Spoken Focus |
|:---:|:---:|:---|:---|:---|
| **01** | `0:00 - 0:30` | `http://localhost:8000` Header & Case Card | Hover green `LIVE_VERIFIED` badge, NMB-204 case card, quarantine badge | The cold-chain safety gap; live Nebius & Tavily provider connection |
| **02** | `0:30 - 0:55` | Temperature Chart & Event Rail | Toggle table, highlight 40-min breach, 10.5°C peak, 10:18 UTC door event | Deterministic Python engine; correlation of IoT logger with dock door |
| **03** | `0:55 - 1:20` | Stage Tracker & Tavily Live Proof Panel | Click "Investigate Excursion", expand Tavily panel, show live queries & URLs | Live Tavily API search; strict domain allowlist (`cdc.gov`, `who.int`) |
| **04** | `1:20 - 1:50` | Hypothesis Board & Skeptic Panel | Show 3 live hypotheses; hover skeptic critique of reefer voltage | NVIDIA Nemotron-70B on Nebius live inference; adversarial falsification |
| **05** | `1:50 - 2:20` | Counterfactual Workbench & Modal | Select 5-min door limit, click replay (40min → 0min); open Review Packet | Sensitivity replay controls; printable review packet with SHA-256 digests |
| **06** | `2:20 - 2:30` | Summary Header & Live Receipts | Show live token usage, round-trip latency (ms), model signature | Closing: IoT reality + Tavily retrieval + Nemotron reasoning on Nebius |

#### Scene 1: The Problem & Live Verified Integration (0:00 - 0:30)
- **Visual:** Browser showing `http://localhost:8000`. Fullscreen at 1920x1080.
- **Onscreen Action:** Cursor points to the green `LIVE_VERIFIED` badge in the header, showing connected status to Nebius Token Factory and Tavily Search. Point to shipment ID `NMB-204` and quarantine status.
- **Spoken Narration:**
  > "Every year, billions of dollars in critical biopharmaceuticals and vaccines are lost to cold-chain temperature excursions during multimodal transit. In high-consequence life sciences, you cannot simply guess whether a shipment is safe, nor can you trust an unconstrained AI model that hallucinates approval. This is ExcursionLens: an evidence-driven, bounded agent for cold-chain forensics, running live on NVIDIA Nemotron-70B via Nebius Token Factory and authoritative live search via Tavily."

#### Scene 2: Deterministic Baseline & Event Alignment (0:30 - 0:55)
- **Visual:** Focus on the Temperature Telemetry Chart and the Custody/Operational Event Rail.
- **Onscreen Action:** Toggle "Show Accessible Table" to show raw timestamps, then inspect the 40-minute breach window peaking at 10.5°C against the 2.0°C to 8.0°C temperature band. Point to the door-open event at 10:18 UTC.
- **Spoken Narration:**
  > "First, the foundation is 100% deterministic code. Before any AI call occurs, our Python domain engine parses the raw sensor time-series. For shipment NMB-204, it identifies an exact 40-minute breach above 8°C, peaking at 10.5°C with an area under the curve of 50.5 degree-minutes. Notice how the timeline aligns custody handshakes with vehicle IoT telemetry: exactly at 10:18 UTC, cargo door sensors trigger at Newburgh Transfer Hub Dock 3 during an unconditioned transfer."

#### Scene 3: Authoritative Live Search via Tavily (0:55 - 1:20)
- **Visual:** Click "Investigate Excursion". The Stage Tracker steps through stages 1 to 4.
- **Onscreen Action:** Expand the Sponsor Integration Proof Panel, highlighting live Tavily search queries, real round-trip latency, and verified source URLs from `cdc.gov` and `who.int`.
- **Spoken Narration:**
  > "Clicking 'Investigate Excursion' triggers our bounded state machine. Stage 4 executes live Tavily searches restricted to strict public health domains—specifically the CDC Vaccine Storage Toolkit and WHO Good Distribution Practices. External content is strictly bounded and hashed to prevent prompt injection, providing live ground-truth reference citations for thermal accumulation limits."

#### Scene 4: Live NVIDIA Nemotron Reasoning & Adversarial Skeptic Pass (1:20 - 1:50)
- **Visual:** Stages 5 and 6 complete. The Hypothesis Board reveals 3 competing hypotheses; the Adversarial Skeptic Panel displays live critique.
- **Onscreen Action:** Cursor points to Hypothesis 1 (Transfer Staging Heat Infiltration) with high confidence, then to Hypothesis 2 (Reefer Power Failure). Hover over the Skeptic Critique showing how reefer bus voltage (12.8V-13.1V) directly refutes power loss. Click on evidence badge `OBS-EXCURSION-01` to show the Evidence Drawer.
- **Spoken Narration:**
  > "In Stages 5 and 6, NVIDIA Nemotron-70B synthesizes three competing causal hypotheses via Nebius Token Factory. Crucially, ExcursionLens runs an adversarial skeptic pass. While an ordinary LLM might speculate that the vehicle's refrigeration unit failed, our skeptic pass cross-checks the reefer alternator telemetry, which recorded steady 12.8 volts, directly falsifying the power loss theory. Every claim is validated against explicit observation IDs."

#### Scene 5: Counterfactual Workbench & Quality Review Packet (1:50 - 2:20)
- **Visual:** Counterfactual Workbench and Review Packet Modal.
- **Onscreen Action:** In the Counterfactual Workbench, select "Expedite Door Closing (5 min limit vs 24 min observed)" and click "Replay Counterfactual". The delta shows simulated excursion duration reduced from 40.0 min to 0.0 min. Then click "Review Packet" to display the full printable quality packet with cryptographic hashes and model signatures.
- **Spoken Narration:**
  > "To evaluate preventive sensitivity controls, our Counterfactual Workbench allows QA engineers to replay interventions. Here, enforcing a 5-minute door closing rule prevents the thermal breach entirely in simulation. Finally, we generate a formal Quality Review Packet, complete with evidence hashes, live Nebius model receipts, and an unbending quarantine boundary. Physical stock remains safely segregated until human QA signs off."

#### Scene 6: Conclusion & System Summary (2:20 - 2:30)
- **Visual:** Return to main header showing clean state, live provider receipts, and version tag.
- **Spoken Narration:**
  > "ExcursionLens bridges physical IoT reality, live Tavily regulatory guidance, and NVIDIA Nemotron reasoning on Nebius Token Factory—transforming cold-chain compliance into an auditable, evidence-driven science. Thank you."
