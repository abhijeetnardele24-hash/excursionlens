# ExcursionLens Submission Readiness Checklist

**Project:** ExcursionLens (Cold-Chain Temperature Excursion Investigation Agent)  
**Hackathon:** Nebius x NVIDIA Hackathon (Devpost)  
**Tracks:** *Best Apps and Agents* (Primary track; *Best Use of Tavily* bonus track omitted pending live credential receipt)  
**Repository:** `https://github.com/abhijeetnardele24-hash/excursionlens`  
**Current Posture:** `INTERNAL_COMPLETE_EXTERNAL_ACTION_REQUIRED`  
*Designed to use NVIDIA Nemotron through Nebius Token Factory. Current committed execution evidence is fixture mode; live verification remains blocked pending credentials.*

> [!NOTE]
> **Evidence Authority Policy:**  
> Committed JSON documents (such as `docs/verification-results.json` or `test-results/coverage.json`) are local snapshots for documentation convenience.  
> The **authoritative verification record** is generated directly within the [GitHub Actions CI Workflow](https://github.com/abhijeetnardele24-hash/excursionlens/actions/workflows/ci.yml) as downloadable artifact `verification-artifacts-<COMMIT_SHA>` (authoritative Linux CI metrics: 165 test cases passing, 92.98% statement coverage, 81.85% unrounded branch coverage under pytest 9.2.0 on Python 3.11.17).

---

## 1. Codebase & Repository Integrity
- [x] Dedicated fresh git repository created exclusively for ExcursionLens.
- [x] Zero history mixing or reuse from prior hackathon projects.
- [x] `.gitignore` properly configured for Python, Node, Vite, and environment files.
- [x] Open-source license added: `LICENSE` (Apache-2.0).
- [x] `.env.example` created without any active or default private credentials.
- [x] Security scan verified 0 exposed secrets across working tree and commit history (`scripts/security_scan.py`).

---

## 2. Master Verification Gates (All Internal Gates Passed)
- [x] **Gate 1 (Python Lint):** Ruff linter clean across `apps/api`, `scripts`, and `benchmark` (0 violations).
- [x] **Gate 2 (Python Typing):** Mypy clean with `--check-untyped-defs` (0 type errors).
- [x] **Gate 3 (Frontend Build):** TypeScript type-check and Vite production build clean (`apps/web/dist`).
- [x] **Gate 4 (Backend Unit & Coverage):** Canonical Pytest suite passing with 165 test cases, 92.98% statement coverage, and 81.85% unrounded branch coverage (90.24% combined coverage under canonical pytest 9.2.0 on Python 3.11.17 with `--cov-branch --cov-fail-under=85` enforcement; evaluated directly in the [GitHub Actions CI Workflow](https://github.com/abhijeetnardele24-hash/excursionlens/actions/workflows/ci.yml)).
- [x] **Gate 5 (Deterministic Benchmark):** 12 of 12 frozen synthetic scenarios passed with 100% mathematical precision (`benchmark/run_benchmark.py`).
- [x] **Gate 6 (Security Scan):** 0 secrets detected.
- [x] **Gate 7 (Playwright E2E & Axe):** 5 logical journeys (25 viewport executions) passed across 5 viewports (320px, 390px, 768px, 1280px, 1920px). Automated Axe scans detected zero violations in tested states across all five configured viewports (automated tests evaluate targeted accessibility rules and do not constitute complete WCAG certification).
- [x] Machine verification receipt generated at `docs/verification-results.json` (`INTERNAL_COMPLETE_EXTERNAL_ACTION_REQUIRED`).

---

## 3. Product Features & Truthful Provider Status
- [x] Canonical NMB-204 case fixture loaded and displayed.
- [x] 100% deterministic excursion detector (40.0-min window, peak 10.5°C, AUC 50.5 degree-minutes).
- [x] Multimodal custody and operational event rail aligned along UTC axis.
- [x] Runtime mode cleanly disentangled: `application_environment` ("local" / "docker" / "production") vs `provider_status` (`NOT_CONFIGURED`, `CONFIGURED_PENDING_VERIFICATION`, `LIVE_VERIFIED`, `PARTIAL_FAILURE`, `DEMO_FIXTURE`, `DEMO_FIXTURE_FALLBACK`).
- [x] Never returns `"mode": "live"` when external keys are absent.
- [x] Deterministic synthetic fixture replay mode verified for Nebius & Tavily.
- [ ] Live Nebius Token Factory inference verification (*BLOCKED pending external credentials*).
- [ ] Live Tavily Search integration verification (*BLOCKED pending external credentials*).
- [x] Adversarial skeptic critique pass cross-referencing vehicle alternator voltage.
- [x] Counterfactual preventive control simulation workbench with typed parameters.
- [x] Printable Quality Review Packet with cryptographic SHA-256 evidence digests.
- [x] Strict Anti-Auto-Release Invariant enforced (`QUARANTINE_PENDING_QUALIFIED_REVIEW`).

---

## 4. Submission Media Assets
- [x] `docs/assets/architecture.png` (2200x1360 retina diagram)
- [x] `docs/assets/excursionlens-devpost-thumbnail.png` (1280x720 Devpost thumbnail)
- [x] `docs/assets/screenshots/01_case_overview.png`
- [x] `docs/assets/screenshots/02_timeline_evidence.png`
- [x] `docs/assets/screenshots/03_hypothesis_board.png`
- [x] `docs/assets/screenshots/04_counterfactual.png`
- [x] `docs/assets/screenshots/05_review_packet.png`

---

## 5. Documentation Deliverables
- [x] `README.md` (comprehensive setup, architecture, and judge walkthrough)
- [x] `docs/ARCHITECTURE.md`
- [x] `docs/EVALUATION.md`
- [x] `docs/SAFETY.md`
- [x] `docs/DATA_SOURCES.md`
- [x] `docs/DEMO_SCRIPT.md` (contains two distinct variants: `FIXTURE_MODE_DRAFT` and `LIVE_VERIFIED_FINAL`)
- [x] `docs/DEVPOST_SUBMISSION.md`
- [x] `docs/TOKEN_FACTORY_FEEDBACK.md`
- [x] `Dockerfile` and `docker-compose.yml`

---

## 6. External Actions & Human Handoff Posture

The system remains in posture `INTERNAL_COMPLETE_EXTERNAL_ACTION_REQUIRED` until external live provider keys are supplied:

- [ ] 1. **Provide Nebius Credential (Optional for Fixture Mode, Required for Live Verified):** Complete Nebius $0 verification card authorization on `tokenfactory.nebius.com` (or await Builder Program manual review) to obtain `NEBIUS_TOKEN_FACTORY_KEY`, then set it via:
  `gh secret set NEBIUS_TOKEN_FACTORY_KEY -R abhijeetnardele24-hash/excursionlens`
- [x] 2. **Tavily Credential:** Bonus track omitted; Tavily search is optional and zero-blocking for primary *Best Apps and Agents* track.
- [ ] 3. **Execute Live Smoke Verification (If Key Configured):** Dispatch `.github/workflows/live-smoke.yml` to obtain live API receipts (`LIVE_TOKEN_FACTORY` or `LIVE_VERIFIED`) with real HTTP latency and token counts.
- [x] 4. **Public Demo Endpoint (REQUIRED):** Verified temporary live public demonstration tunnel active at `https://exercise-streams-manhattan-submitting.trycloudflare.com` (verified via `scripts/deploy_smoke.py`, recorded in `docs/deployment-receipt.json` as `LIVE_DEPLOYED` in `DEMO_FIXTURE` mode).
- [x] 5. **Configure Domain & TLS:** Verified active with valid Cloudflare TLS.
- [x] 6. **Verify Public Endpoints:** Confirmed `/api/health`, `/api/meta`, frontend `/`, and canonical case `/api/cases/CASE-NMB-204` respond with expected `application_environment: production`, `provider_status: NOT_CONFIGURED`, and `live_execution_verified: false`.
- [ ] 7. **Record Demo Video:** Record the ~2:30 video demonstration according to `docs/DEMO_SCRIPT.md` (using `FIXTURE_MODE_DRAFT` for honest fixture review, or `LIVE_VERIFIED_FINAL` if keys are configured).
- [ ] 8. **Upload Demo Video:** Host video on Public YouTube (duration strictly under 3:00).
- [ ] 9. **Populate Devpost Submission Form:** Copy submission title, tagline, tracks, and markdown from `docs/DEVPOST_SUBMISSION.md`, along with the public GitHub repo URL and `docs/assets/excursionlens-devpost-thumbnail.png`.
- [ ] 10. **Submit on Devpost:** Submit final entry on the Devpost hackathon portal before the hackathon deadline.
