# ExcursionLens: Official Video Demonstration Source Package

**Target Duration:** 2 minutes 40 seconds (Strict target: 2:35–2:50 | Hard maximum: 3:00)  
**Publishing Requirement:** Public YouTube video (URL to replace `[PUBLIC_YOUTUBE_URL_PLACEHOLDER]` in `docs/DEVPOST_SUBMISSION.md`)  
**Target Application URL:** `http://localhost:8000` (run via `docker compose up --build`) or public HTTPS deployment URL  
**Target Hardware / Screen Resolution:** 1920×1080 Full HD (16:9), 100% zoom  
**Recording Mode:** Fullscreen browser window with bookmarks, search bar, and extensions hidden  

---

## 1. Video Asset Specifications

| Asset Type | File Path / Identifier | Description & Purpose |
|:---|:---|:---|
| **Thumbnail** | `docs/assets/excursionlens-devpost-thumbnail.png` | 1280×720 high-contrast thumbnail, legible at 350px card width |
| **Scene 1 Screenshot** | `docs/assets/screenshots/01_case_overview.png` | Case overview card, NMB-204 metadata, initial quarantine posture |
| **Scene 2 Screenshot** | `docs/assets/screenshots/02_timeline_evidence.png` | Temperature chart, breach window (40.0 min, 10.5°C peak), custody rail |
| **Scene 3 Screenshot** | `docs/assets/screenshots/03_hypothesis_board.png` | Competing hypotheses board with adversarial skeptic critique |
| **Scene 4 Screenshot** | `docs/assets/screenshots/04_counterfactual.png` | Counterfactual workbench simulating 5-min door limit |
| **Scene 5 Screenshot** | `docs/assets/screenshots/05_review_packet.png` | Printable quarantine review packet modal with SHA-256 evidence digests |
| **Architecture** | `docs/assets/architecture.png` | End-to-end 8-stage bounded state-machine pipeline |

---

## 2. Pre-Recording Technical Checklist

- [ ] Run `docker compose up --build` or launch `http://localhost:8000`.
- [ ] Open in Chrome / Chromium at 1920×1080 fullscreen.
- [ ] Ensure browser developer tools are closed.
- [ ] Ensure OS notifications, taskbar, and personal bookmarks are hidden.
- [ ] Verify audio input is clear and normalized (no echo, clean speech rate).
- [ ] Prepare mouse clicks smoothly with intentional pauses (1-2 seconds per major interaction).

---

## 3. Timestamped Storyboard & Exact Interaction Script

### Scene 1: The Cold-Chain Forensics Challenge (0:00 – 0:30)
- **Timecode:** `0:00 - 0:30` (30 seconds)
- **Onscreen Visual:** Browser showing `http://localhost:8000`. Top header and Case Summary Card.
- **Physical Interactions:**
  1. Hover over the Case ID **`NMB-204`** and product title: *Pentavalent Biologic Vaccine Lot 88B*.
  2. Point to the **2.0°C to 8.0°C** allowable thermal control band.
  3. Point to the red alert banner: **`QUARANTINE PENDING QUALIFIED REVIEW`**.
  4. Point to the Header Status Pill: shows truthful runtime posture (`NOT_CONFIGURED` / `DEMO_FIXTURE` in fixture mode, or `LIVE_TOKEN_FACTORY` when keys are provided).
- **Spoken Narration (Voiceover):**
  > "Every year, up to fifty percent of critical vaccines and temperature-sensitive biologics are wasted globally due to cold-chain failures and shipping excursions. When an IoT temperature logger alarms at the receiving dock, quality teams face an impossible dilemma: release compromised medication to patients, or destroy millions of dollars of viable product because they cannot isolate whether surface heat penetrated the liquid core.
  >
  > This is ExcursionLens: an evidence-first operational forensics agent built to use NVIDIA Nemotron through Nebius Token Factory and authoritative web search through Tavily. Notice our header: ExcursionLens operates fail-closed, never fabricating provider responses."

---

### Scene 2: Deterministic Baseline & Event Rail Alignment (0:30 – 0:55)
- **Timecode:** `0:30 - 0:55` (25 seconds)
- **Onscreen Visual:** Focus on the Temperature Telemetry Chart and the Multimodal Event Rail.
- **Physical Interactions:**
  1. Scroll down smoothly to the interactive temperature curve.
  2. Click **"Show Accessible Table"** to reveal the raw tabular time-series readings.
  3. Hover over the breach window: highlight the 40-minute breach starting at 10:15 UTC and peaking at **10.5°C** (50.5°C·min Area Under the Curve).
  4. Point to the aligned custody event rail: highlight the Newburgh Hub unconditioned cross-dock transfer and open bay door logged at **10:18 UTC**.
- **Spoken Narration (Voiceover):**
  > "Our foundation is 100% deterministic code. Zero generative tokens are used for temperature calculations. The Python domain engine calculates an exact 40-minute breach above 8°C, reaching a peak temperature of 10.5°C with an Area Under the Curve of 50.5 degree-minutes.
  >
  > When aligned with custody logs along a continuous UTC axis, the temperature spike correlates exactly with an unconditioned cross-dock transfer and open bay doors at Newburgh Hub at 10:18 UTC."

---

### Scene 3: Bounded State Machine & Sponsor Proof Moment (0:55 – 1:25)
- **Timecode:** `0:55 - 1:25` (30 seconds)
- **Onscreen Visual:** Action Bar and Stage Tracker.
- **Physical Interactions:**
  1. Click the primary button: **`Investigate Excursion`**.
  2. Watch the Stage Tracker stream through stages 1 to 4 (`VALIDATE_SCHEMA` $\to$ `NORMALIZE_SERIES` $\to$ `DETECT_EXCURSION` $\to$ `TAVILY_GUIDANCE`).
  3. Expand the **Provider & Retrieval Proof Panel**:
     - Highlight **Nebius Token Factory** and the target model **`nvidia/llama-3.1-nemotron-70b-instruct`**.
     - Highlight **Tavily Search** and the strict domain allowlist (`cdc.gov`, `fda.gov`, `who.int`).
  4. Click on the **Evidence Drawer** to show the official regulatory guidance records from CDC and WHO.
- **Spoken Narration (Voiceover):**
  > "Clicking 'Investigate Excursion' triggers our bounded state machine. Stage 4 queries public health guidelines using Tavily, strictly allowlisted to CDC, FDA, and WHO domains.
  >
  > Opening the Evidence Drawer reveals cryptographically digested guidance records. ExcursionLens maintains strict provenance: verified summaries are explicitly labeled to ensure quality teams are never misled."

---

### Scene 4: Competing Hypotheses & Adversarial Skeptic Pass (1:25 – 1:55)
- **Timecode:** `1:25 - 1:55` (30 seconds)
- **Onscreen Visual:** Stages 5 and 6 complete. Hypothesis Board and Adversarial Skeptic Panel.
- **Physical Interactions:**
  1. Show the 3 generated hypotheses on the board:
     - Hypothesis 1: *Transfer Staging Ambient Heat Penetration* (Leading).
     - Hypothesis 2: *Refrigeration Compressor Auxiliary Power Failure* (Refuted).
     - Hypothesis 3: *Surface Sensor Detachment* (Alternative).
  2. Hover over the **Skeptic Critique** on Hypothesis 2: point to the vehicle alternator telemetry badge showing steady **12.8V to 13.1V**.
  3. Point out how the Skeptic directly falsifies auxiliary power loss.
- **Spoken Narration (Voiceover):**
  > "Stages 5 and 6 execute our dual-pass causal engine, powered by NVIDIA Nemotron-70B on Nebius. First, generator synthesis produces three competing hypotheses. Next, an adversarial skeptic pass tests each hypothesis against telemetry facts.
  >
  > While a naive LLM might blame refrigeration failure, the skeptic analyzes the truck alternator telemetry: voltage remained rock-steady at 12.8 to 13.1 volts, directly refuting compressor power loss and isolating dock infiltration as the primary root cause. Strict regex validators trap any hallucinated release claims."

---

### Scene 5: Counterfactual Workbench & Quarantine Review Packet (1:55 – 2:25)
- **Timecode:** `1:55 - 2:25` (30 seconds)
- **Onscreen Visual:** Counterfactual Workbench and Review Packet Modal.
- **Physical Interactions:**
  1. Scroll to the **Counterfactual Workbench**.
  2. Select the intervention parameter: *Expedite Door Closing (5 min limit vs 24 min observed)*.
  3. Click **`Replay Counterfactual`**: point to the dynamic delta showing duration dropping from **40.0 min to 0.0 min**.
  4. Click **`Review Packet`**: the full-screen modal opens showing the complete audit trail, observation IDs, and SHA-256 evidence hashes.
  5. Scroll to the bottom of the modal: show the strict **Anti-Auto-Release Invariant** requiring human QA sign-off.
- **Spoken Narration (Voiceover):**
  > "To assist quality teams with preventive actions, our Counterfactual Workbench simulates operational interventions. Enforcing a 5-minute dock door limit completely eliminates the excursion in simulation, providing clear Corrective and Preventive Action insights.
  >
  > Finally, ExcursionLens compiles a comprehensive Quality Review Packet with cryptographic SHA-256 digests. Under our Anti-Auto-Release Invariant, the system is architecturally barred from authorizing product release—the disposition terminates strictly in Quarantine Pending Qualified Review."

---

### Scene 6: Conclusion & System Boundaries (2:25 – 2:40)
- **Timecode:** `2:25 - 2:40` (15 seconds)
- **Onscreen Visual:** Return to the top dashboard view and audit footer.
- **Physical Interactions:**
  1. Close the Review Packet modal.
  2. Scroll smoothly back to the top header showing the completed investigation state and audit footer.
- **Spoken Narration (Voiceover):**
  > "ExcursionLens bridges physical IoT telemetry, deterministic mathematics, and adversarial causal reasoning—turning biopharmaceutical cold-chain compliance into an auditable science. Thank you."

---

## 4. Post-Recording Quality & Privacy Verification

Before uploading to YouTube:
1. **Duration Check:** Confirm total video runtime is between **2:30 and 2:50** (strictly under the 3:00 hard cutoff).
2. **Audio Sync Check:** Verify narration audio matches cursor interactions on screen.
3. **No Private Secrets:** Verify zero API keys, personal user paths (e.g. `C:\Users\...`), or internal tokens appeared on screen.
4. **Visibility:** Set YouTube video visibility to **Public** (or Unlisted if permitted by Devpost hackathon rules).
5. **URL Handoff:** Copy the YouTube watch URL (e.g. `https://youtu.be/...`) and paste it into `docs/DEVPOST_SUBMISSION.md` replacing `[PUBLIC_YOUTUBE_URL_PLACEHOLDER]`.
