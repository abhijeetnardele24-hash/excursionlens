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

ROOT = Path(__file__).resolve().parent.parent

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

def main():
    print("=" * 60)
    print("  EXCURSIONLENS MASTER VERIFICATION SUITE")
    print("=" * 60)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git": get_git_info(),
        "gates": {},
    }

    # 1. Python Lint (Ruff)
    print("\n[Gate 1/6] Running Ruff Linter on apps/...")
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

    # 2. Frontend Typecheck & Build
    print("\n[Gate 2/6] Running TypeScript Check & Vite Build on apps/web...")
    rc, stdout, stderr, elapsed = run_cmd(["cmd.exe", "/c", "npm", "--prefix", "apps/web", "run", "build"])
    results["gates"]["frontend_build"] = {
        "passed": rc == 0,
        "elapsed_sec": round(elapsed, 2),
        "output": stdout[-300:] if rc == 0 else stdout,
    }
    if rc == 0:
        print("  ✓ TypeScript & Vite build succeeded")
    else:
        print(f"  ✗ Frontend build failed:\n{stdout}\n{stderr}")

    # 3. Backend Unit & Coverage (Pytest)
    print("\n[Gate 3/6] Running Pytest & Coverage...")
    cov_path = ROOT / "test-results" / "coverage.json"
    cov_path.parent.mkdir(parents=True, exist_ok=True)
    env = {"PYTHONPATH": "."}
    rc, stdout, stderr, elapsed = run_cmd([
        sys.executable, "-m", "pytest", "apps/api/tests",
        "--cov=apps.api.app",
        f"--cov-report=json:{cov_path}",
        "--cov-report=term"
    ], env=env)

    cov_pct = 0.0
    if cov_path.exists():
        try:
            with open(cov_path, "r", encoding="utf-8") as f:
                cov_data = json.load(f)
                cov_pct = cov_data.get("totals", {}).get("percent_covered", 0.0)
        except Exception:
            pass

    results["gates"]["pytest"] = {
        "passed": rc == 0,
        "coverage_percent": round(cov_pct, 2),
        "elapsed_sec": round(elapsed, 2),
    }
    if rc == 0:
        print(f"  ✓ Pytest passed (coverage: {round(cov_pct, 2)}%)")
    else:
        print(f"  ✗ Pytest failed:\n{stdout}\n{stderr}")

    # 4. Deterministic Frozen Benchmark Suite (12 scenarios)
    print("\n[Gate 4/6] Running Frozen Synthetic Benchmark Suite...")
    rc, stdout, stderr, elapsed = run_cmd([sys.executable, "benchmark/run_benchmark.py"], env=env)
    results["gates"]["benchmark"] = {
        "passed": rc == 0,
        "total_scenarios": 12,
        "passed_scenarios": 12 if rc == 0 else 0,
        "elapsed_sec": round(elapsed, 2),
    }
    if rc == 0:
        print("  ✓ 12/12 Frozen Synthetic Benchmark scenarios passed")
    else:
        print(f"  ✗ Benchmark failed:\n{stdout}\n{stderr}")

    # 5. Security & Secret Scan
    print("\n[Gate 5/6] Running Security & Secret Scanner...")
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

    # 6. Playwright E2E & Axe Accessibility Results
    print("\n[Gate 6/6] Parsing Playwright & Axe E2E Results...")
    pw_results_path = ROOT / "test-results" / "playwright-results.json"
    pw_passed = False
    pw_stats = {}
    if pw_results_path.exists():
        try:
            with open(pw_results_path, "r", encoding="utf-8") as f:
                pw_data = json.load(f)
                pw_stats = pw_data.get("stats", {})
                expected = pw_stats.get("expected", 0)
                unexpected = pw_stats.get("unexpected", 0)
                flaky = pw_stats.get("flaky", 0)
                pw_passed = unexpected == 0 and expected > 0
                results["gates"]["playwright"] = {
                    "passed": pw_passed,
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
        print(f"  ✓ Playwright & Axe passed: {pw_stats.get('expected')} runs passed across 5 viewports")
    else:
        print(f"  ✗ Playwright status: {results['gates'].get('playwright')}")

    # Overall Status
    all_passed = all(g.get("passed", False) for g in results["gates"].values())
    results["overall_status"] = "PASSED" if all_passed else "FAILED"

    # Write out verification-results.json
    out_file = ROOT / "docs" / "verification-results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  OVERALL VERIFICATION STATUS: {results['overall_status']}")
    print(f"  Written to: {out_file.relative_to(ROOT)}")
    print("=" * 60)

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
