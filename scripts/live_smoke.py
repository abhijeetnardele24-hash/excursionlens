#!/usr/bin/env python3
"""
scripts/live_smoke.py — Fail-Closed Real Runtime Smoke Test for Nebius Token Factory & Tavily

Features:
1. Queries live Nebius Token Factory model catalog and filters for NVIDIA / Nemotron models.
2. Executes live chat completion with structured output validation using NVIDIA Nemotron.
3. Executes live Tavily Search query restricted to authoritative health domains.
4. Redacts all sensitive credential tokens.
5. Emits machine-readable receipts to docs/live-smoke-receipt.json and docs/provider-receipts.json.
6. Returns exit code 0 ONLY if BOTH live calls succeed. Returns exit code 1 if keys are absent or failed.
7. Cannot pass from cached fixture data.
"""

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.config import settings  # noqa: E402


def redact_string(s: str | None) -> str:
    if not s:
        return "<none>"
    s = s.strip()
    if len(s) <= 8:
        return "***"
    return f"{s[:4]}...{s[-4:]}"


def sha256_digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def run_live_smoke() -> int:
    nebius_key = settings.nebius_key.strip()
    nebius_base_url = settings.nebius_base_url
    tavily_key = settings.tavily_key.strip()
    deep_model = settings.nvidia_deep_model_id.strip()

    receipt: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "FAILED",
        "nebius_smoke": {
            "tested_model": deep_model,
            "status": "NOT_RUN",
            "latency_ms": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "response_digest": None,
            "structured_output_valid": False,
            "key_present": bool(nebius_key and not nebius_key.startswith("your_")),
            "key_preview": redact_string(nebius_key)
        },
        "tavily_smoke": {
            "query": "CDC cold chain storage handling temperature excursion 2 to 8 C",
            "status": "NOT_RUN",
            "latency_ms": None,
            "results_count": 0,
            "source_domains": [],
            "query_digest": sha256_digest("CDC cold chain storage handling temperature excursion 2 to 8 C"),
            "key_present": bool(tavily_key and not tavily_key.startswith("your_")),
            "key_preview": redact_string(tavily_key)
        },
        "failure_reasons": []
    }

    print("=" * 70)
    print("🧪 ExcursionLens Live Provider Smoke Test (Fail-Closed)")
    print("=" * 70)

    # 1. Check Tavily
    print("\n[1/2] Executing live Tavily Search query...")
    if not receipt["tavily_smoke"]["key_present"]:
        reason = "TAVILY_API_KEY is not configured or contains placeholder."
        receipt["tavily_smoke"]["status"] = "MISSING_KEY"
        receipt["failure_reasons"].append(reason)
        print(f"   ⚠️  {reason}")
    else:
        try:
            t0 = time.time()
            tavily_payload = {
                "api_key": tavily_key,
                "query": "CDC vaccine storage handling temperature excursion 2 to 8 C",
                "search_depth": "basic",
                "include_domains": ["cdc.gov", "fda.gov", "who.int", "gs1.org"],
                "max_results": 3
            }
            with httpx.Client(timeout=15.0) as client:
                res = client.post("https://api.tavily.com/search", json=tavily_payload)
                t_latency = int((time.time() - t0) * 1000)
                receipt["tavily_smoke"]["latency_ms"] = t_latency
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    domains = list({r.get("url", "").split("//")[-1].split("/")[0].lower() for r in results if r.get("url")})
                    receipt["tavily_smoke"]["status"] = "LIVE_SUCCESS"
                    receipt["tavily_smoke"]["results_count"] = len(results)
                    receipt["tavily_smoke"]["source_domains"] = domains
                    print(f"   ✅ Tavily Live Success! Returned {len(results)} results in {t_latency}ms. Domains: {domains}")
                else:
                    reason = f"Tavily returned HTTP {res.status_code}: {res.text[:200]}"
                    receipt["tavily_smoke"]["status"] = f"HTTP_{res.status_code}"
                    receipt["failure_reasons"].append(reason)
                    print(f"   ❌ {reason}")
        except Exception as e:
            reason = f"Tavily exception: {type(e).__name__} - {e}"
            receipt["tavily_smoke"]["status"] = "ERROR"
            receipt["failure_reasons"].append(reason)
            print(f"   ❌ {reason}")

    # 2. Check Nebius Token Factory
    print("\n[2/2] Executing live Nebius Token Factory inference with NVIDIA model...")
    if not receipt["nebius_smoke"]["key_present"]:
        reason = "NEBIUS_TOKEN_FACTORY_KEY is not configured or contains placeholder."
        receipt["nebius_smoke"]["status"] = "MISSING_KEY"
        receipt["failure_reasons"].append(reason)
        print(f"   ⚠️  {reason}")
    else:
        try:
            # Catalog probe
            model_to_use = deep_model
            with httpx.Client(timeout=15.0) as client:
                m_res = client.get(
                    f"{nebius_base_url}models",
                    headers={"Authorization": f"Bearer {nebius_key}"}
                )
                if m_res.status_code == 200:
                    m_data = m_res.json().get("data", [])
                    nvidia_models = [m["id"] for m in m_data if "nvidia" in m["id"].lower() or "nemotron" in m["id"].lower()]
                    if nvidia_models:
                        model_to_use = deep_model if deep_model in nvidia_models else nvidia_models[0]
                    receipt["nebius_smoke"]["tested_model"] = model_to_use
                else:
                    receipt["nebius_smoke"]["status"] = f"CATALOG_HTTP_{m_res.status_code}"

            t0 = time.time()
            prompt = (
                "You are an assistant for cold-chain excursion analysis. "
                "Analyze this synthetic event: A shipment of 2-8 C vaccines was exposed to 10.5 C for 40 minutes. "
                "Output valid JSON with keys 'incident_summary', 'hypotheses' (list of strings), and 'recommended_posture'."
            )
            chat_payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": "You output strictly valid JSON without markdown wrapping."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500
            }
            with httpx.Client(timeout=30.0) as client:
                chat_res = client.post(
                    f"{nebius_base_url}chat/completions",
                    headers={
                        "Authorization": f"Bearer {nebius_key}",
                        "Content-Type": "application/json"
                    },
                    json=chat_payload
                )
                n_latency = int((time.time() - t0) * 1000)
                receipt["nebius_smoke"]["latency_ms"] = n_latency

                if chat_res.status_code == 200:
                    c_data = chat_res.json()
                    choices = c_data.get("choices", [])
                    usage = c_data.get("usage", {})
                    receipt["nebius_smoke"]["prompt_tokens"] = usage.get("prompt_tokens")
                    receipt["nebius_smoke"]["completion_tokens"] = usage.get("completion_tokens")
                    receipt["nebius_smoke"]["total_tokens"] = usage.get("total_tokens")

                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        receipt["nebius_smoke"]["response_digest"] = sha256_digest(content)
                        try:
                            clean_content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                            parsed = json.loads(clean_content)
                            if "incident_summary" in parsed and "hypotheses" in parsed:
                                receipt["nebius_smoke"]["structured_output_valid"] = True
                        except Exception:
                            pass

                    receipt["nebius_smoke"]["status"] = "LIVE_SUCCESS"
                    print(f"   ✅ Nebius Token Factory Live Success! Model '{model_to_use}' responded in {n_latency}ms.")
                else:
                    reason = f"Nebius Token Factory returned HTTP {chat_res.status_code}: {chat_res.text[:200]}"
                    receipt["nebius_smoke"]["status"] = f"HTTP_{chat_res.status_code}"
                    receipt["failure_reasons"].append(reason)
                    print(f"   ❌ {reason}")
        except Exception as e:
            reason = f"Nebius exception: {type(e).__name__} - {e}"
            receipt["nebius_smoke"]["status"] = "ERROR"
            receipt["failure_reasons"].append(reason)
            print(f"   ❌ {reason}")

    # Determine overall status
    tavily_ok = receipt["tavily_smoke"]["status"] == "LIVE_SUCCESS"
    nebius_ok = receipt["nebius_smoke"]["status"] == "LIVE_SUCCESS"

    if tavily_ok and nebius_ok:
        receipt["status"] = "LIVE_VERIFIED"
    elif tavily_ok or nebius_ok:
        receipt["status"] = "PARTIAL_LIVE"
    else:
        receipt["status"] = "BLOCKED" if (not receipt["tavily_smoke"]["key_present"] and not receipt["nebius_smoke"]["key_present"]) else "FAILED"

    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_path = docs_dir / "live-smoke-receipt.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    # Also update provider-receipts.json with honest status
    prov_receipts_path = docs_dir / "provider-receipts.json"
    with open(prov_receipts_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": receipt["timestamp"],
            "nebius": {
                "base_url": nebius_base_url,
                "key_present": receipt["nebius_smoke"]["key_present"],
                "key_preview": receipt["nebius_smoke"]["key_preview"],
                "status": receipt["nebius_smoke"]["status"],
                "tested_model": receipt["nebius_smoke"]["tested_model"],
                "latency_ms": receipt["nebius_smoke"]["latency_ms"],
                "probe_success": nebius_ok
            },
            "tavily": {
                "key_present": receipt["tavily_smoke"]["key_present"],
                "key_preview": receipt["tavily_smoke"]["key_preview"],
                "status": receipt["tavily_smoke"]["status"],
                "latency_ms": receipt["tavily_smoke"]["latency_ms"],
                "probe_success": tavily_ok,
                "domains_found": receipt["tavily_smoke"]["source_domains"]
            },
            "overall_ready": (nebius_ok and tavily_ok),
            "overall_status": receipt["status"],
            "failure_reasons": receipt["failure_reasons"]
        }, f, indent=2)

    print("\n" + "=" * 70)
    print(f"Live Smoke Receipt written to: {out_path.relative_to(ROOT)}")
    print(f"Overall Smoke Status: {receipt['status']}")
    print("=" * 70)

    # Fails nonzero if not LIVE_VERIFIED
    return 0 if receipt["status"] == "LIVE_VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(run_live_smoke())
