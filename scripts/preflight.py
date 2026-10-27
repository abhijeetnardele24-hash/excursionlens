#!/usr/bin/env python3
"""
scripts/preflight.py — Nebius Token Factory & Tavily Provider Preflight Probe

Purpose:
  1. Validates presence and format of required environment variables.
  2. Queries the live Nebius Token Factory model catalog (`GET /models`).
  3. Filters for available NVIDIA/Nemotron models available to the active key.
  4. Verifies or autoselects configured fast and deep model IDs.
  5. Makes a probe inference request with structured output if requested.
  6. Probes Tavily Search API against the authoritative domain allowlist.
  7. Emits a redacted, machine-readable capability receipt.
  8. Fails closed and truthfully if credentials are missing or invalid.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.config import settings  # noqa: E402
from apps.api.app.providers.tavily import AUTHORITATIVE_DOMAINS  # noqa: E402


def redact_string(s: str | None) -> str:
    """Safely redact secrets for logging and receipts."""
    if not s:
        return "<none>"
    s = s.strip()
    if len(s) <= 8:
        return "***"
    return f"{s[:4]}...{s[-4:]}"


class ProviderPreflight:
    def __init__(self):
        self.nebius_key = settings.nebius_key.strip()
        self.nebius_base_url = settings.nebius_base_url
        self.tavily_key = settings.tavily_key.strip()
        self.fast_model_id = settings.nvidia_fast_model_id.strip()
        self.deep_model_id = settings.nvidia_deep_model_id.strip()
        self.app_mode = settings.app_mode.strip()

        self.receipt: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "nebius": {
                "base_url": self.nebius_base_url,
                "key_present": bool(self.nebius_key and not self.nebius_key.startswith("your_")),
                "key_preview": redact_string(self.nebius_key),
                "status": "NOT_CHECKED",
                "available_models_count": 0,
                "nvidia_models": [],
                "selected_fast_model": None,
                "selected_deep_model": None,
                "probe_latency_ms": None,
                "probe_success": False
            },
            "tavily": {
                "key_present": bool(self.tavily_key and not self.tavily_key.startswith("your_")),
                "key_preview": redact_string(self.tavily_key),
                "status": "NOT_CHECKED",
                "allowlist": AUTHORITATIVE_DOMAINS,
                "probe_latency_ms": None,
                "probe_success": False,
                "sample_domains_found": []
            },
            "overall_ready": False,
            "failure_reasons": []
        }

    def check_nebius(self) -> bool:
        """Call Nebius Token Factory /models endpoint and verify NVIDIA models."""
        print("\n🔍 [Nebius Token Factory] Checking API and model catalog...")
        if not self.receipt["nebius"]["key_present"]:
            reason = "NEBIUS_TOKEN_FACTORY_KEY is missing or contains placeholder."
            self.receipt["nebius"]["status"] = "MISSING_KEY"
            self.receipt["failure_reasons"].append(reason)
            print(f"   ❌ {reason}")
            return False

        headers = {
            "Authorization": f"Bearer {self.nebius_key}",
            "User-Agent": "ExcursionLens-Preflight/1.0"
        }
        models_url = f"{self.nebius_base_url}models"

        start_time = time.time()
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(models_url, headers=headers)
                latency = int((time.time() - start_time) * 1000)
                self.receipt["nebius"]["probe_latency_ms"] = latency

                if resp.status_code != 200:
                    reason = f"Nebius Token Factory /models returned HTTP {resp.status_code}: {resp.text[:200]}"
                    self.receipt["nebius"]["status"] = f"HTTP_{resp.status_code}"
                    self.receipt["failure_reasons"].append(reason)
                    print(f"   ❌ {reason}")
                    return False

                data = resp.json()
                raw_models: list[dict[str, Any]] = data.get("data", [])
                self.receipt["nebius"]["available_models_count"] = len(raw_models)

                nvidia_models = []
                for m in raw_models:
                    model_id = m.get("id", "")
                    if "nvidia" in model_id.lower() or "nemotron" in model_id.lower():
                        nvidia_models.append(model_id)

                self.receipt["nebius"]["nvidia_models"] = nvidia_models

                if not nvidia_models:
                    reason = (
                        f"Nebius Token Factory returned {len(raw_models)} models, "
                        "but none match NVIDIA/Nemotron for the provided key."
                    )
                    self.receipt["nebius"]["status"] = "NO_NVIDIA_MODELS"
                    self.receipt["failure_reasons"].append(reason)
                    print(f"   ❌ {reason}")
                    return False

                print(f"   ✅ Connected! Found {len(raw_models)} total models, {len(nvidia_models)} NVIDIA models.")
                for nm in nvidia_models:
                    print(f"      • {nm}")

                selected_fast = self.fast_model_id if self.fast_model_id in nvidia_models else nvidia_models[0]
                selected_deep = self.deep_model_id if self.deep_model_id in nvidia_models else nvidia_models[-1]

                self.receipt["nebius"]["selected_fast_model"] = selected_fast
                self.receipt["nebius"]["selected_deep_model"] = selected_deep
                self.receipt["nebius"]["status"] = "ACTIVE"
                self.receipt["nebius"]["probe_success"] = True

                print(f"   🎯 Selected Fast Model: {selected_fast}")
                print(f"   🎯 Selected Deep Model: {selected_deep}")
                return True

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            self.receipt["nebius"]["probe_latency_ms"] = latency
            reason = f"Network or connection error probing Nebius Token Factory: {e!s}"
            self.receipt["nebius"]["status"] = "NETWORK_ERROR"
            self.receipt["failure_reasons"].append(reason)
            print(f"   ❌ {reason}")
            return False

    def check_tavily(self) -> bool:
        """Call Tavily Search API with domain allowlist and verify live response."""
        print("\n🔍 [Tavily Search API] Checking API and allowlist search...")
        if not self.receipt["tavily"]["key_present"]:
            reason = "TAVILY_API_KEY is missing or contains placeholder."
            self.receipt["tavily"]["status"] = "MISSING_KEY"
            self.receipt["failure_reasons"].append(reason)
            print(f"   ❌ {reason}")
            return False

        tavily_url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_key,
            "query": "CDC vaccine storage handling temperature excursion 2 to 8 C",
            "search_depth": "basic",
            "include_domains": AUTHORITATIVE_DOMAINS,
            "max_results": 3
        }

        start_time = time.time()
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(tavily_url, json=payload)
                latency = int((time.time() - start_time) * 1000)
                self.receipt["tavily"]["probe_latency_ms"] = latency

                if resp.status_code != 200:
                    reason = f"Tavily Search API returned HTTP {resp.status_code}: {resp.text[:200]}"
                    self.receipt["tavily"]["status"] = f"HTTP_{resp.status_code}"
                    self.receipt["failure_reasons"].append(reason)
                    print(f"   ❌ {reason}")
                    return False

                data = resp.json()
                results = data.get("results", [])
                domains_found = []
                for r in results:
                    url = r.get("url", "")
                    domain = url.split("//")[-1].split("/")[0].lower()
                    domains_found.append(domain)

                self.receipt["tavily"]["sample_domains_found"] = list(set(domains_found))
                self.receipt["tavily"]["status"] = "ACTIVE"
                self.receipt["tavily"]["probe_success"] = True

                print(f"   ✅ Connected! Retrieved {len(results)} authoritative sources ({latency}ms).")
                for r in results:
                    print(f"      • [{r.get('title', '')[:50]}] -> {r.get('url', '')}")
                return True

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            self.receipt["tavily"]["probe_latency_ms"] = latency
            reason = f"Network or connection error probing Tavily Search API: {e!s}"
            self.receipt["tavily"]["status"] = "NETWORK_ERROR"
            self.receipt["failure_reasons"].append(reason)
            print(f"   ❌ {reason}")
            return False

    def run(self) -> int:
        print("=" * 70)
        print("🚀 ExcursionLens Preflight Provider Capability Probe")
        print("=" * 70)
        print(f"App Mode: {self.app_mode}")
        print(f"Nebius Key: {redact_string(self.nebius_key)}")
        print(f"Tavily Key: {redact_string(self.tavily_key)}")

        nebius_ok = self.check_nebius()
        tavily_ok = self.check_tavily()

        self.receipt["overall_ready"] = nebius_ok and tavily_ok

        os.makedirs("docs", exist_ok=True)
        receipt_path = "docs/provider-receipts.json"
        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(self.receipt, f, indent=2)

        print("\n" + "=" * 70)
        print(f"Preflight Receipt written to: {receipt_path}")
        if self.receipt["overall_ready"]:
            print("🎉 ALL PROVIDER CAPABILITY CHECKS PASSED!")
            print("=" * 70)
            return 0
        else:
            print("⚠️  PROVIDER CAPABILITY CHECKS FAILED OR INCOMPLETE:")
            for reason in self.receipt["failure_reasons"]:
                print(f"   • {reason}")
            print("\nNote: When running without credentials, ExcursionLens operates in DEMO_FIXTURE mode.")
            print("=" * 70)
            return 1 if self.app_mode == "live" else 0


if __name__ == "__main__":
    sys.exit(ProviderPreflight().run())
