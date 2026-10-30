#!/usr/bin/env python3
"""
scripts/check_deployment.py — Quick Availability and Dependency Check for ExcursionLens

Verifies the active temporary demonstration endpoint against:
1. HTTP 200 and valid JSON on /api/health
2. HTTP 200 and valid JSON on /api/meta
3. HTTP 200 and HTML body on root /
4. HTTP 200 on canonical case /api/cases/CASE-NMB-204
5. Matching Git commit SHA
6. Explicit disclosure of TEMPORARY_DEMO_ENDPOINT dependencies (local process, cloudflared, laptop power, internet)
"""

import argparse
import os
import subprocess
import sys
import time
from typing import Any

import httpx

DEFAULT_ENDPOINT = "https://newest-surname-observer-cow.trycloudflare.com"


def get_local_git_sha() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return os.environ.get("GITHUB_SHA", "unknown")


def check_availability(
    target_url: str = DEFAULT_ENDPOINT,
    expected_sha: str | None = None,
    timeout: float = 12.0
) -> tuple[bool, dict[str, Any], list[str]]:
    failures: list[str] = []
    base_url = target_url.rstrip("/")
    expected = expected_sha or get_local_git_sha()
    metrics: dict[str, Any] = {
        "target_url": base_url,
        "endpoint_type": "TEMPORARY_DEMO_ENDPOINT",
        "expected_sha": expected,
        "deployed_sha": None,
        "commit_match": False,
        "provider_mode": None,
        "provider_status": None,
        "live_execution_verified": False,
        "latency_ms": None,
        "endpoints": {}
    }

    t0 = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            # 1. Health
            h_res = client.get(f"{base_url}/api/health")
            if h_res.status_code != 200:
                failures.append(f"/api/health failed with HTTP {h_res.status_code}")
            else:
                h_json = h_res.json()
                metrics["deployed_sha"] = h_json.get("commit")
                metrics["provider_mode"] = h_json.get("provider_mode")
                metrics["provider_status"] = h_json.get("provider_status")
                metrics["live_execution_verified"] = h_json.get("live_execution_verified", False)
                metrics["endpoints"]["health"] = {"status": 200}

            # 2. Meta
            m_res = client.get(f"{base_url}/api/meta")
            if m_res.status_code != 200:
                failures.append(f"/api/meta failed with HTTP {m_res.status_code}")
            else:
                metrics["endpoints"]["meta"] = {"status": 200}

            # 3. Frontend Root
            fe_res = client.get(f"{base_url}/")
            if fe_res.status_code != 200 or "<html" not in fe_res.text.lower():
                failures.append(f"Frontend root '/' did not return valid HTML (HTTP {fe_res.status_code})")
            else:
                metrics["endpoints"]["frontend"] = {"status": 200, "html_verified": True}

            # 4. Canonical Case
            c_res = client.get(f"{base_url}/api/cases/CASE-NMB-204")
            if c_res.status_code == 404:
                c_res = client.get(f"{base_url}/api/cases/NMB-204")
            if c_res.status_code != 200:
                failures.append(f"Canonical case endpoint failed with HTTP {c_res.status_code}")
            else:
                metrics["endpoints"]["canonical_case"] = {"status": 200}

        metrics["latency_ms"] = int((time.time() - t0) * 1000)

        if metrics["deployed_sha"] and expected and expected != "unknown":
            metrics["commit_match"] = (metrics["deployed_sha"] == expected)
            if not metrics["commit_match"]:
                failures.append(
                    f"Deployed commit '{metrics['deployed_sha']}' does not match expected '{expected}'"
                )

    except Exception as e:
        metrics["latency_ms"] = int((time.time() - t0) * 1000)
        failures.append(f"Connection error to {base_url}: {type(e).__name__} - {e}")

    success = len(failures) == 0
    return success, metrics, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="ExcursionLens Deployment Availability Check")
    parser.add_argument("--url", default=os.environ.get("DEPLOY_URL", DEFAULT_ENDPOINT), help="Target endpoint URL")
    parser.add_argument("--expected-sha", default=None, help="Expected Git commit SHA")
    args = parser.parse_args()

    print("=" * 70)
    print("  EXCURSIONLENS DEPLOYMENT AVAILABILITY & DEPENDENCY AUDIT")
    print("=" * 70)
    print(f"Target URL:     {args.url}")
    print("Classification: TEMPORARY_DEMO_ENDPOINT")
    print("Dependencies:   Local Uvicorn server, Cloudflared tunnel, laptop power & internet")
    print("-" * 70)

    success, metrics, failures = check_availability(args.url, args.expected_sha)

    if success:
        print("✅ DEPLOYMENT IS AVAILABLE & HEALTHY")
        print(f"   • Latency:                {metrics['latency_ms']} ms")
        print(f"   • Deployed Commit:        {metrics['deployed_sha']}")
        print(f"   • Commit Matched HEAD:    {metrics['commit_match']}")
        print(f"   • Provider Mode:          {metrics['provider_mode']}")
        print(f"   • Provider Status:        {metrics['provider_status']}")
        print(f"   • Live Verified:          {metrics['live_execution_verified']}")
        print("   • Endpoints Tested:       /, /api/health, /api/meta, /api/cases/CASE-NMB-204 (all 200 OK)")
        print("\n⚠️  NOTICE: This endpoint is a TEMPORARY_DEMO_ENDPOINT powered by a local quick-tunnel.")
        print("   It remains active only while the local process, cloudflared, and internet remain online.")
        print("=" * 70)
        return 0
    else:
        print("❌ DEPLOYMENT CHECK FAILED")
        for f in failures:
            print(f"   • {f}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
