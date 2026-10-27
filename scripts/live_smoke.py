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
from urllib.parse import urlsplit

import httpx

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.app.config import settings  # noqa: E402

AUTHORITATIVE_DOMAINS = [
    "cdc.gov",
    "fda.gov",
    "who.int",
    "gs1.org"
]


def redact_string(s: str | None) -> str:
    if not s:
        return "<none>"
    s = s.strip()
    if len(s) <= 8:
        return "***"
    return f"{s[:4]}...{s[-4:]}"


def sha256_digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify_tavily(
    tavily_key: str,
    client: httpx.Client | None = None
) -> tuple[dict[str, Any], list[str]]:
    """Probes Tavily search endpoint with strict allowlist, https, and digest validation."""
    query = "CDC vaccine storage handling temperature excursion 2 to 8 C"
    query_dig = sha256_digest(query)
    receipt: dict[str, Any] = {
        "query": query,
        "query_digest": query_dig,
        "status": "NOT_RUN",
        "latency_ms": None,
        "results_count": 0,
        "source_domains": [],
        "source_digests": [],
        "key_present": bool(tavily_key and not tavily_key.startswith("your_") and len(tavily_key) > 8),
        "key_preview": redact_string(tavily_key)
    }
    failures: list[str] = []

    if not receipt["key_present"]:
        receipt["status"] = "MISSING_KEY"
        failures.append("TAVILY_API_KEY is not configured or contains placeholder.")
        return receipt, failures

    payload = {
        "api_key": tavily_key,
        "query": query,
        "search_depth": "basic",
        "include_domains": AUTHORITATIVE_DOMAINS,
        "max_results": 3
    }

    t0 = time.time()
    try:
        http_client = client or httpx.Client(timeout=15.0)
        close_client = client is None
        try:
            res = http_client.post("https://api.tavily.com/search", json=payload)
        finally:
            if close_client:
                http_client.close()

        latency = int((time.time() - t0) * 1000)
        receipt["latency_ms"] = latency

        if res.status_code != 200:
            receipt["status"] = f"HTTP_{res.status_code}"
            failures.append(f"Tavily returned HTTP {res.status_code}: {res.text[:200]}")
            return receipt, failures

        data = res.json()
        raw_results = data.get("results", [])
        if not isinstance(raw_results, list):
            receipt["status"] = "MALFORMED_RESPONSE"
            failures.append("Tavily response 'results' field is not a list.")
            return receipt, failures

        retained_results = []
        source_digests = []
        source_domains = set()

        for idx, r in enumerate(raw_results):
            raw_url = r.get("url", "")
            try:
                parsed = urlsplit(raw_url)
            except Exception:
                continue

            # Must be HTTPS
            if parsed.scheme.lower() != "https":
                continue

            host = parsed.netloc.lower().split(":")[0]
            # Must be allowlisted
            if not any(host == ad or host.endswith("." + ad) for ad in AUTHORITATIVE_DOMAINS):
                continue

            content = r.get("content", "").strip()
            content_dig = sha256_digest(content)
            source_digests.append(content_dig)
            source_domains.add(host)
            retained_results.append(r)

        receipt["results_count"] = len(retained_results)
        receipt["source_domains"] = sorted(source_domains)
        receipt["source_digests"] = source_digests

        if len(retained_results) == 0:
            receipt["status"] = "NO_VALID_RESULTS"
            failures.append("Tavily returned 0 usable results matching HTTPS and the domain allowlist.")
            return receipt, failures

        receipt["status"] = "LIVE_SUCCESS"
        return receipt, failures

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        receipt["latency_ms"] = latency
        receipt["status"] = "ERROR"
        failures.append(f"Tavily exception: {type(e).__name__} - {e}")
        return receipt, failures


def verify_nebius(
    nebius_key: str,
    nebius_base_url: str,
    preferred_deep_model: str,
    client: httpx.Client | None = None
) -> tuple[dict[str, Any], list[str]]:
    """Probes Nebius model catalog, selects NVIDIA model, and runs structured completion validation."""
    receipt: dict[str, Any] = {
        "tested_model": preferred_deep_model,
        "selected_catalog_model": None,
        "status": "NOT_RUN",
        "latency_ms": None,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "response_digest": None,
        "structured_output_valid": False,
        "key_present": bool(nebius_key and not nebius_key.startswith("your_") and len(nebius_key) > 8),
        "key_preview": redact_string(nebius_key)
    }
    failures: list[str] = []

    if not receipt["key_present"]:
        receipt["status"] = "MISSING_KEY"
        failures.append("NEBIUS_TOKEN_FACTORY_KEY is not configured or contains placeholder.")
        return receipt, failures

    base_url = nebius_base_url.rstrip("/") + "/"
    headers = {
        "Authorization": f"Bearer {nebius_key}",
        "Content-Type": "application/json"
    }

    t0 = time.time()
    try:
        http_client = client or httpx.Client(timeout=30.0)
        close_client = client is None
        try:
            # 1. Model Catalog Probe
            cat_res = http_client.get(f"{base_url}models", headers=headers)
            if cat_res.status_code != 200:
                receipt["status"] = f"CATALOG_HTTP_{cat_res.status_code}"
                failures.append(f"Nebius models endpoint returned HTTP {cat_res.status_code}: {cat_res.text[:200]}")
                return receipt, failures

            cat_data = cat_res.json()
            models_list = cat_data.get("data", [])
            if not isinstance(models_list, list) or len(models_list) == 0:
                receipt["status"] = "EMPTY_CATALOG"
                failures.append("Nebius model catalog returned empty 'data' array.")
                return receipt, failures

            nvidia_models = [
                m.get("id", "") for m in models_list
                if "nvidia" in m.get("id", "").lower() or "nemotron" in m.get("id", "").lower()
            ]

            if not nvidia_models:
                receipt["status"] = "NO_NVIDIA_MODELS"
                failures.append("Nebius model catalog returned 0 NVIDIA or Nemotron models.")
                return receipt, failures

            # Select an actually returned model from the catalog
            if preferred_deep_model in nvidia_models:
                selected_model = preferred_deep_model
            else:
                # Prefer 70b variant if available, else first
                matches_70b = [m for m in nvidia_models if "70b" in m.lower()]
                selected_model = matches_70b[0] if matches_70b else nvidia_models[0]

            receipt["selected_catalog_model"] = selected_model
            receipt["tested_model"] = selected_model

            # 2. Live Chat Completion with Structured Validation
            prompt = (
                "You are an assistant for cold-chain excursion analysis. "
                "Analyze this synthetic event: A shipment of 2-8 C vaccines was exposed to 10.5 C for 40 minutes. "
                "Output valid JSON with keys 'incident_summary', 'hypotheses' (list of strings), and 'recommended_posture'."
            )
            chat_payload = {
                "model": selected_model,
                "messages": [
                    {"role": "system", "content": "You output strictly valid JSON without markdown wrapping."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 500
            }

            chat_res = http_client.post(
                f"{base_url}chat/completions",
                headers=headers,
                json=chat_payload
            )
            latency = int((time.time() - t0) * 1000)
            receipt["latency_ms"] = latency

            if chat_res.status_code != 200:
                receipt["status"] = f"COMPLETION_HTTP_{chat_res.status_code}"
                failures.append(f"Nebius chat completion returned HTTP {chat_res.status_code}: {chat_res.text[:200]}")
                return receipt, failures

            c_data = chat_res.json()
            choices = c_data.get("choices", [])
            usage = c_data.get("usage", {})
            receipt["prompt_tokens"] = usage.get("prompt_tokens")
            receipt["completion_tokens"] = usage.get("completion_tokens")
            receipt["total_tokens"] = usage.get("total_tokens")

            if not isinstance(choices, list) or len(choices) == 0:
                receipt["status"] = "EMPTY_CHOICES"
                failures.append("Nebius chat completion returned empty choices.")
                return receipt, failures

            choice_obj = choices[0]
            content = choice_obj.get("message", {}).get("content", "")
            if not isinstance(content, str) or not content.strip():
                receipt["status"] = "EMPTY_CONTENT"
                failures.append("Nebius completion content was empty.")
                return receipt, failures

            receipt["response_digest"] = sha256_digest(content)

            # Structured JSON parsing and schema validation
            clean_content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                parsed = json.loads(clean_content)
            except Exception as jerr:
                receipt["status"] = "MALFORMED_JSON"
                failures.append(f"Nebius output failed JSON decoding: {jerr}")
                return receipt, failures

            if not isinstance(parsed, dict):
                receipt["status"] = "INVALID_ROOT_TYPE"
                failures.append("Nebius JSON output is not a dictionary/object.")
                return receipt, failures

            # Field checks
            inc_summary = parsed.get("incident_summary")
            if not isinstance(inc_summary, str) or not inc_summary.strip():
                receipt["status"] = "MISSING_FIELD_INCIDENT_SUMMARY"
                failures.append("Missing or invalid 'incident_summary' in Nebius output.")
                return receipt, failures

            hypotheses = parsed.get("hypotheses")
            if not isinstance(hypotheses, list) or len(hypotheses) == 0 or not all(isinstance(h, str) and h.strip() for h in hypotheses):
                receipt["status"] = "MISSING_FIELD_HYPOTHESES"
                failures.append("Missing or invalid 'hypotheses' list in Nebius output.")
                return receipt, failures

            rec_posture = parsed.get("recommended_posture")
            if not isinstance(rec_posture, str) or not rec_posture.strip():
                receipt["status"] = "MISSING_FIELD_RECOMMENDED_POSTURE"
                failures.append("Missing or invalid 'recommended_posture' in Nebius output.")
                return receipt, failures

            receipt["structured_output_valid"] = True
            receipt["status"] = "LIVE_SUCCESS"
            return receipt, failures

        finally:
            if close_client:
                http_client.close()

    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        receipt["latency_ms"] = latency
        receipt["status"] = "ERROR"
        failures.append(f"Nebius exception: {type(e).__name__} - {e}")
        return receipt, failures


def run_live_smoke() -> int:
    nebius_key = settings.nebius_key.strip()
    nebius_base_url = settings.nebius_base_url
    tavily_key = settings.tavily_key.strip()
    deep_model = settings.nvidia_deep_model_id.strip()

    print("=" * 70)
    print("🧪 ExcursionLens Live Provider Smoke Test (Fail-Closed)")
    print("=" * 70)

    # 1. Check Tavily
    print("\n[1/2] Executing live Tavily Search query...")
    tavily_receipt, tavily_failures = verify_tavily(tavily_key)
    if tavily_receipt["status"] == "LIVE_SUCCESS":
        print(f"   ✅ Tavily Live Success! Returned {tavily_receipt['results_count']} results in {tavily_receipt['latency_ms']}ms.")
        print(f"      Domains: {tavily_receipt['source_domains']}")
    else:
        print(f"   ❌ Tavily failed ({tavily_receipt['status']}): {tavily_failures}")

    # 2. Check Nebius Token Factory
    print("\n[2/2] Executing live Nebius Token Factory inference with NVIDIA model...")
    nebius_receipt, nebius_failures = verify_nebius(nebius_key, nebius_base_url, deep_model)
    if nebius_receipt["status"] == "LIVE_SUCCESS":
        print(f"   ✅ Nebius Token Factory Live Success! Model '{nebius_receipt['tested_model']}' responded in {nebius_receipt['latency_ms']}ms.")
    else:
        print(f"   ❌ Nebius failed ({nebius_receipt['status']}): {nebius_failures}")

    all_failures = tavily_failures + nebius_failures
    tavily_ok = tavily_receipt["status"] == "LIVE_SUCCESS"
    nebius_ok = nebius_receipt["status"] == "LIVE_SUCCESS"

    if tavily_ok and nebius_ok:
        overall_status = "LIVE_VERIFIED"
    elif tavily_ok or nebius_ok:
        overall_status = "PARTIAL_LIVE"
    else:
        overall_status = "BLOCKED" if (not tavily_receipt["key_present"] and not nebius_receipt["key_present"]) else "FAILED"

    receipt = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": overall_status,
        "nebius_smoke": nebius_receipt,
        "tavily_smoke": tavily_receipt,
        "failure_reasons": all_failures
    }

    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_path = docs_dir / "live-smoke-receipt.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

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

    # Returns 0 ONLY if LIVE_VERIFIED
    return 0 if receipt["status"] == "LIVE_VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(run_live_smoke())
