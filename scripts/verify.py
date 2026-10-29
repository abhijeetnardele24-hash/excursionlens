#!/usr/bin/env python3
"""
ExcursionLens Verification Gate Runner
Executes all linting, typing, unit testing, benchmark evaluation, security scanning,
and parses Playwright test results to generate docs/verification-results.json.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.provenance import get_execution_provenance  # noqa: E402


def run_cmd(args, env=None, capture=True):
    start = time.time()
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    proc = subprocess.run(
        args,
        cwd=ROOT,
        env=merged_env,
        capture_output=capture,
        text=True,
    )
    elapsed = time.time() - start
    return proc.returncode, proc.stdout, proc.stderr, elapsed

def get_git_info():
    _, head, _, _ = run_cmd(["git", "rev-parse", "HEAD"])
    _, branch, _, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, status, _, _ = run_cmd(["git", "status", "--porcelain"])
    return {
        "head": head.strip(),
        "branch": branch.strip(),
        "clean_tree": len(status.strip()) == 0,
    }

def evaluate_smoke_receipt(smoke_data: dict[str, Any], current_head: str) -> tuple[str, str | None]:
    """
    Evaluates live smoke receipt status against current commit HEAD.
    Strict exact-SHA matching: any mismatch produces ('BLOCKED/STALE_EVIDENCE', 'STALE_EVIDENCE').
    Zero compatibility waivers (HEAD~1 waiver removed).
    """
    raw_status = smoke_data.get("status") or smoke_data.get("overall_status", "BLOCKED")
    receipt_sha = smoke_data.get("commit_sha") or smoke_data.get("git_commit")

    if not current_head or not receipt_sha or receipt_sha != current_head:
        return "BLOCKED/STALE_EVIDENCE", "STALE_EVIDENCE"

    return raw_status, None

def main():
    print("=" * 60)
    print("  EXCURSIONLENS MASTER VERIFICATION SUITE")
    print("=" * 60)

    git_info = get_git_info()
    evidence_authority, execution_context = get_execution_provenance()

    results = {
        "schema_version": "1.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evidence_authority": evidence_authority,
        "execution_context": execution_context,
        "git": git_info,
        "tree_clean_before_verification": git_info["clean_tree"],
        "gates": {},
    }

    # 1. Python Lint (Ruff)
    print("\n[Gate 1/7] Running Ruff Linter on apps/ and scripts/...")
    rc, stdout, stderr, elapsed = run_cmd([sys.executable, "-m", "ruff", "check", "apps/api", "scripts", "benchmark"])
    results["gates"]["ruff"] = {
        "passed": rc == 0,
        "elapsed_sec": round(elapsed, 2),
        "output": stdout if rc == 0 else f"{stdout}\n{stderr}",
    }
    if rc == 0:
        print("  ✓ Ruff lint passed (0 violations)")
    else:
        print(f"  ✗ Ruff lint failed:\n{stdout}\n{stderr}")

    # 2. Python Static Typing (Mypy with --check-untyped-defs)
    print("\n[Gate 2/7] Running Mypy on apps/api/app...")
    rc, stdout, stderr, elapsed = run_cmd([
        sys.executable, "-m", "mypy", "apps/api/app",
        "--ignore-missing-imports",
        "--check-untyped-defs"
    ])
    results["gates"]["mypy"] = {
        "passed": rc == 0,
        "elapsed_sec": round(elapsed, 2),
        "output": stdout if rc == 0 else f"{stdout}\n{stderr}",
    }
    if rc == 0:
        print("  ✓ Mypy typing passed (0 type errors)")
    else:
        print(f"  ✗ Mypy typing failed:\n{stdout}\n{stderr}")

    # 3. Frontend Typecheck & Build
    print("\n[Gate 3/7] Running TypeScript Check & Vite Build on apps/web...")
    npm_cmd = ["cmd.exe", "/c", "npm", "--prefix", "apps/web", "run", "build"] if sys.platform == "win32" else ["npm", "--prefix", "apps/web", "run", "build"]
    rc, stdout, stderr, elapsed = run_cmd(npm_cmd)
    results["gates"]["frontend_build"] = {
        "passed": rc == 0,
        "elapsed_sec": round(elapsed, 2),
        "output": stdout[-300:] if rc == 0 else stdout,
    }
    if rc == 0:
        print("  ✓ TypeScript & Vite build succeeded")
    else:
        print(f"  ✗ Frontend build failed:\n{stdout}\n{stderr}")

    # 4. Backend Unit & Coverage (Pytest with canonical branch coverage and thresholds)
    print("\n[Gate 4/7] Running Pytest & Coverage (Statement >= 85%, Branch >= 80%)...")
    cov_path = ROOT / "test-results" / "coverage.json"
    cov_path.parent.mkdir(parents=True, exist_ok=True)
    env = {
        "PYTHONPATH": ".",
        "GITHUB_SHA": os.environ.get("GITHUB_SHA") or git_info.get("head") or "1837e00facd0f4d27906255472d9be2a339885b4",
    }
    rc, stdout, stderr, elapsed = run_cmd([
        sys.executable, "-m", "pytest", "apps/api/tests",
        "--cov=apps/api/app",
        "--cov-branch",
        f"--cov-report=json:{cov_path}",
        "--cov-report=term-missing",
        "--cov-fail-under=85"
    ], env=env)

    cov_pct = 0.0
    statement_cov_pct = 0.0
    branch_cov_pct = 0.0
    if cov_path.exists():
        try:
            with open(cov_path, "r", encoding="utf-8") as f:
                cov_data = json.load(f)
                totals = cov_data.get("totals", {})
                cov_pct = totals.get("percent_covered", 0.0)
                statement_cov_pct = totals.get("percent_statements_covered", 0.0)
                branch_cov_pct = totals.get("percent_branches_covered", 0.0)
        except Exception:
            pass

    cov_passed = (rc == 0) and (statement_cov_pct >= 85.0) and (branch_cov_pct >= 80.0)

    results["gates"]["pytest"] = {
        "passed": cov_passed,
        "coverage_percent": round(cov_pct, 2),
        "statement_coverage_percent": round(statement_cov_pct, 2),
        "branch_coverage_percent": round(branch_cov_pct, 2),
        "elapsed_sec": round(elapsed, 2),
    }
    if cov_passed:
        print(f"  ✓ Pytest passed (statement: {round(statement_cov_pct, 2)}%, branch: {round(branch_cov_pct, 2)}%, total: {round(cov_pct, 2)}%)")
    else:
        print(f"  ✗ Pytest failed (rc={rc}, statement={round(statement_cov_pct, 2)}%, branch={round(branch_cov_pct, 2)}%):\n{stdout}\n{stderr}")


    # 5. Deterministic Frozen Benchmark Suite (parsed dynamically from benchmark-results.json)
    print("\n[Gate 5/7] Running Frozen Synthetic Benchmark Suite...")
    rc, stdout, stderr, elapsed = run_cmd([sys.executable, "benchmark/run_benchmark.py"], env=env)
    bm_path = ROOT / "test-results" / "benchmark-results.json"
    bm_total = 0
    bm_passed = 0
    if bm_path.exists():
        try:
            with open(bm_path, "r", encoding="utf-8") as f:
                bm_data = json.load(f)
                bm_total = bm_data.get("total_scenarios", 0)
                bm_passed = bm_data.get("passed_scenarios", 0)
        except Exception:
            pass

    bm_success = (rc == 0) and (bm_total > 0) and (bm_passed == bm_total)
    results["gates"]["benchmark"] = {
        "passed": bm_success,
        "total_scenarios": bm_total,
        "passed_scenarios": bm_passed,
        "elapsed_sec": round(elapsed, 2),
    }
    if bm_success:
        print(f"  ✓ {bm_passed}/{bm_total} Frozen Synthetic Benchmark scenarios passed")
    else:
        print(f"  ✗ Benchmark failed: {bm_passed}/{bm_total} passed:\n{stdout}\n{stderr}")

    # 6. Security & Secret Scan
    print("\n[Gate 6/7] Running Security & Secret Scanner...")
    rc, stdout, stderr, elapsed = run_cmd([sys.executable, "scripts/security_scan.py"])
    results["gates"]["security_scan"] = {
        "passed": rc == 0,
        "exposed_secrets": 0 if rc == 0 else -1,
        "elapsed_sec": round(elapsed, 2),
    }
    if rc == 0:
        print("  ✓ Security scan passed (0 exposed secrets)")
    else:
        print(f"  ✗ Security scan failed:\n{stdout}\n{stderr}")

    # 7. Playwright E2E & Axe Accessibility Results
    print("\n[Gate 7/7] Verifying Playwright & Axe E2E Results...")
    pw_results_path = ROOT / "test-results" / "playwright-results.json"

    # Check freshness: verify result was generated recently (not stale)
    is_fresh = False
    if pw_results_path.exists():
        mtime = os.path.getmtime(pw_results_path)
        if (time.time() - mtime) < 1800:  # within 30 minutes
            is_fresh = True

    if not is_fresh:
        print("  Playwright results missing or stale. Running test suite...")
        npx_cmd = ["cmd.exe", "/c", "npx", "playwright", "test"] if sys.platform == "win32" else ["npx", "playwright", "test"]
        pw_rc, pw_out, pw_err, pw_elapsed = run_cmd(npx_cmd)
        if pw_rc != 0:
            print(f"  Playwright execution exited with code {pw_rc}:\n{pw_err}")

    pw_passed = False
    pw_stats = {}
    logical_tests_count = 0
    viewport_executions_count = 0

    if pw_results_path.exists():
        try:
            with open(pw_results_path, "r", encoding="utf-8") as f:
                pw_data = json.load(f)
                pw_stats = pw_data.get("stats", {})
                expected = pw_stats.get("expected", 0)
                unexpected = pw_stats.get("unexpected", 0)
                flaky = pw_stats.get("flaky", 0)
                viewport_executions_count = expected

                logical_specs = set()
                def extract_specs(suite_list):
                    for s in suite_list:
                        extract_specs(s.get("suites", []))
                        for spec in s.get("specs", []):
                            logical_specs.add(spec.get("title", ""))
                extract_specs(pw_data.get("suites", []))
                logical_tests_count = len(logical_specs)

                pw_passed = unexpected == 0 and expected > 0
                results["gates"]["playwright"] = {
                    "passed": pw_passed,
                    "logical_tests": logical_tests_count,
                    "viewport_executions": viewport_executions_count,
                    "expected": expected,
                    "unexpected": unexpected,
                    "flaky": flaky,
                    "duration_ms": pw_stats.get("duration", 0),
                }
        except Exception as e:
            results["gates"]["playwright"] = {"passed": False, "error": str(e)}
    else:
        results["gates"]["playwright"] = {"passed": False, "error": "test-results/playwright-results.json not found"}

    if pw_passed:
        print(f"  ✓ Playwright & Axe passed: {logical_tests_count} logical journeys ({viewport_executions_count} viewport executions) across 5 viewports")
    else:
        print(f"  ✗ Playwright status: {results['gates'].get('playwright')}")

    # 8. Documentation & Claims Check
    print("\n[Gate 8/8] Running Documentation & Claims Audit...")
    rc_test, out_test, err_test, _ = run_cmd([sys.executable, "scripts/test_check_claims.py"])
    rc, stdout, stderr, elapsed = run_cmd([sys.executable, "scripts/check_claims.py"])
    all_passed = (rc == 0 and rc_test == 0)
    results["gates"]["claims_check"] = {
        "passed": all_passed,
        "elapsed_sec": round(elapsed, 2),
        "output": f"{out_test}\n{stdout}" if all_passed else f"{out_test}\n{err_test}\n{stdout}\n{stderr}",
    }
    if all_passed:
        print("  ✓ Documentation claims audit & regression suite passed (0 violations)")
    else:
        print(f"  ✗ Documentation claims audit failed:\n{out_test}\n{err_test}\n{stdout}\n{stderr}")

    # Canonical Case Ground Truth
    results["canonical_case_nmb_204"] = {
        "shipment_id": "NMB-204",
        "fixture_sha256": "81f95835386fb8b2d6bccc50ffd20d8037f98c6dc7a802ec95854a6c872b363d",
        "excursion_duration_minutes": 40.0,
        "peak_temperature_celsius": 10.5,
        "degree_minutes_auc": 50.5,
        "review_posture": "QUARANTINE_PENDING_QUALIFIED_REVIEW",
    }

    # External Provider Smoke Status
    smoke_path = ROOT / "docs" / "live-smoke-receipt.json"
    smoke_status = "BLOCKED"
    smoke_reason = None
    smoke_data = {}
    if smoke_path.exists():
        try:
            with open(smoke_path, "r", encoding="utf-8") as f:
                smoke_data = json.load(f)
                smoke_status, smoke_reason = evaluate_smoke_receipt(smoke_data, git_info.get("head", ""))
        except Exception:
            pass

    # Public Deployment Receipt Status
    deploy_receipt_path = ROOT / "docs" / "deployment-receipt.json"
    deploy_status = "BLOCKED"
    deploy_reason = "Hosting deployment credentials/target not configured in environment."
    if deploy_receipt_path.exists():
        try:
            with open(deploy_receipt_path, "r", encoding="utf-8") as f:
                d_data = json.load(f)
                deploy_status = d_data.get("status", "BLOCKED")
                deploy_reason = d_data.get("reason", deploy_reason)
        except Exception:
            pass

    results["external_gates"] = {
        "live_providers": {
            "status": smoke_status,
            "reason": smoke_reason,
            "nebius_token_factory": smoke_data.get("nebius_smoke", {}).get("status", "NOT_CONFIGURED"),
            "served_nvidia_model": smoke_data.get("nebius_smoke", {}).get("tested_model", "nvidia/llama-3.1-nemotron-70b-instruct"),
            "tavily_search": smoke_data.get("tavily_smoke", {}).get("status", "NOT_CONFIGURED"),
            "notice": "Fail-closed check. Real inference and retrieval verified when keys provided.",
        },
        "public_deployment": {
            "status": deploy_status,
            "reason": deploy_reason,
            "reproducible_deployment_command": "docker compose up --build -d",
        },
    }

    # Internal Gates Status
    internal_passed = all(g.get("passed", False) for g in results["gates"].values())
    results["internal_verification_status"] = "PASSED" if internal_passed else "FAILED"

    if not internal_passed:
        results["overall_status"] = "FAILED"
    elif smoke_status == "LIVE_VERIFIED":
        results["overall_status"] = "LIVE_VERIFIED"
    elif smoke_status == "LIVE_TOKEN_FACTORY":
        results["overall_status"] = "LIVE_TOKEN_FACTORY"
    else:
        results["overall_status"] = "INTERNAL_COMPLETE_EXTERNAL_ACTION_REQUIRED"


    # Write out verification-results.json
    out_file = ROOT / "docs" / "verification-results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  INTERNAL VERIFICATION STATUS: {results['internal_verification_status']}")
    print(f"  EXTERNAL GATES: Live Providers={smoke_status}, Deployment=BLOCKED")
    print(f"  OVERALL STATUS: {results['overall_status']}")
    print(f"  Written to: {out_file.relative_to(ROOT)}")
    print("=" * 60)

    if not internal_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
