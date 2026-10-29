"""
apps/api/app/providers/tavily.py — Tavily Search Integration & Source Normalization

Searches authoritative public health and standards domains:
- cdc.gov (Vaccine storage and handling toolkit)
- fda.gov (ICH Q1 stability & temperature excursion guidance)
- who.int (Controlled temperature chain & immunization supply guidelines)
- gs1.org (Healthcare barcode & shipment traceability standards)

Produces normalized SourceRecord items with SHA-256 digests and explicit retrieval receipts.
"""

import hashlib
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from ..domain.models import SourceRecord

AUTHORITATIVE_DOMAINS = [
    "cdc.gov",
    "fda.gov",
    "who.int",
    "gs1.org"
]


def is_valid_guidance_url(raw_url: str, allowed_domains: list[str] = AUTHORITATIVE_DOMAINS) -> bool:
    """Validates authoritative guidance URLs strictly requiring HTTPS, valid hostname, and no userinfo."""
    if not raw_url or not isinstance(raw_url, str):
        return False
    try:
        parsed = urlparse(raw_url.strip())
    except Exception:
        return False

    if parsed.scheme.lower() != "https":
        return False
    if parsed.username is not None or parsed.password is not None or "@" in (parsed.netloc or ""):
        return False
    try:
        _ = parsed.port
    except ValueError:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False
    hostname = hostname.lower().strip()
    return any(hostname == ad or hostname.endswith("." + ad) for ad in allowed_domains)


# Canonical pre-vetted public reference guidance for offline benchmark evaluation
CACHED_AUTHORITATIVE_GUIDANCE: list[dict[str, Any]] = [
    {
        "id": "SRC-CDC-01",
        "url": "https://www.cdc.gov/vaccines/hcp/storage-handling/",
        "title": "CDC Vaccine Storage and Handling Clinical Guidance",
        "domain": "cdc.gov",
        "published_or_updated_at": None,
        "snippet": (
            "Clinical guidance for vaccine storage and handling: in the event of a temperature excursion, "
            "immediately separate and store affected vaccines at recommended temperatures (2°C to 8°C), clearly "
            "label them 'DO NOT USE', and contact the manufacturer or immunization program for disposition "
            "guidance prior to administration."
        ),
        "query": "CDC vaccine storage handling temperature excursion 2 to 8 C",
        "source_mode": "VERIFIED_FIXTURE",
        "excerpt_kind": "PARAPHRASE",
        "verified_at": "2026-10-29",
        "verification_note": (
            "Verified via official HTTPS GET (HTTP 200). Summary paraphrases official CDC clinical "
            "storage recommendations; not a verbatim quotation."
        ),
    },
    {
        "id": "SRC-FDA-01",
        "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/q1ar2-stability-testing-new-drug-substances-and-products",
        "title": "Q1A(R2) Stability Testing of New Drug Substances and Products | FDA",
        "domain": "fda.gov",
        "published_or_updated_at": "2003-11",
        "snippet": (
            "FDA/ICH Q1A(R2) stability testing guidance establishes that formal stability profiles under "
            "accelerated conditions evaluate short-term deviations outside declared labeled storage conditions "
            "(e.g., 2°C to 8°C). Any excursion during distribution requires documented assessment against "
            "manufacturer stability data prior to lot disposition."
        ),
        "query": "FDA ICH stability testing temperature excursion refrigerated biologics",
        "source_mode": "VERIFIED_FIXTURE",
        "excerpt_kind": "PARAPHRASE",
        "verified_at": "2026-10-29",
        "verification_note": (
            "Verified via official HTTPS GET (HTTP 200). Summary paraphrases core ICH/FDA stability "
            "principles; not a verbatim quotation."
        ),
    },
    {
        "id": "SRC-WHO-01",
        "url": "https://www.who.int/teams/immunization-vaccines-and-biologicals/essential-programme-on-immunization/supply-chain/controlled-temperature-chain-(ctc)",
        "title": "WHO Controlled Temperature Chain (CTC) Guidance | Essential Programme on Immunization",
        "domain": "who.int",
        "published_or_updated_at": None,
        "snippet": (
            "WHO Controlled Temperature Chain supply chain guidance: temperature monitoring during transit "
            "transfers requires secondary verification of internal product temperature before releasing "
            "quarantined batches. Surface thermal readings during unmonitored transfer windows can diverge "
            "from core product temperature depending on container insulation and packout."
        ),
        "query": "WHO controlled temperature chain transport transfer guidelines",
        "source_mode": "VERIFIED_FIXTURE",
        "excerpt_kind": "PARAPHRASE",
        "verified_at": "2026-10-29",
        "verification_note": (
            "Verified via official HTTPS GET (HTTP 200). Summary paraphrases WHO CTC operational transfer "
            "guidance; not a verbatim quotation."
        ),
    },
]


def sha256_digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class TavilySearchProvider:
    def __init__(self, api_key: str = "", app_mode: str = "live"):
        self.api_key = api_key.strip()
        self.app_mode = app_mode.lower()
        self.has_key = bool(self.api_key and not self.api_key.startswith("your_") and len(self.api_key) > 8)

    def probe_connectivity(self) -> dict[str, Any]:
        """Probes Tavily search endpoint to verify live API key authorization."""
        start_time = time.time()
        if not self.has_key:
            return {
                "status": "NOT_CONFIGURED",
                "provider": "Tavily",
                "latency_ms": 0,
                "allowlist": AUTHORITATIVE_DOMAINS,
                "error_category": "MISSING_KEY",
                "failure_reason": "TAVILY_API_KEY is not configured or contains placeholder."
            }

        payload = {
            "api_key": self.api_key,
            "query": "CDC cold chain vaccine storage handling 2 to 8 C",
            "search_depth": "basic",
            "include_domains": AUTHORITATIVE_DOMAINS,
            "max_results": 1
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post("https://api.tavily.com/search", json=payload)
                latency = int((time.time() - start_time) * 1000)

                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    domains_found = list({urlparse(r.get("url", "")).netloc.lower() for r in results if r.get("url")})
                    return {
                        "status": "LIVE_SUCCESS",
                        "provider": "Tavily",
                        "latency_ms": latency,
                        "allowlist": AUTHORITATIVE_DOMAINS,
                        "sample_domains_found": domains_found,
                        "error_category": None,
                        "failure_reason": None
                    }
                else:
                    return {
                        "status": "FAILED",
                        "provider": "Tavily",
                        "latency_ms": latency,
                        "allowlist": AUTHORITATIVE_DOMAINS,
                        "error_category": f"HTTP_{resp.status_code}",
                        "failure_reason": f"Tavily endpoint returned HTTP {resp.status_code}: {resp.text[:200]}"
                    }
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "FAILED",
                "provider": "Tavily",
                "latency_ms": latency,
                "allowlist": AUTHORITATIVE_DOMAINS,
                "error_category": type(e).__name__,
                "failure_reason": f"Connection exception probing Tavily endpoint: {e}"
            }

    def search_guidance(self, query: str, max_results: int = 3) -> tuple[list[SourceRecord], dict[str, Any]]:
        """Search authoritative guidance. In live mode with keys, makes real HTTPS call; in fixture mode, returns verified cached records."""
        start_time = time.time()
        retrieval_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 1. Attempt live call if key exists
        if self.has_key:
            try:
                tavily_payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_domains": AUTHORITATIVE_DOMAINS,
                    "max_results": max_results
                }
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post("https://api.tavily.com/search", json=tavily_payload)
                    latency_ms = int((time.time() - start_time) * 1000)

                    if resp.status_code == 200:
                        data = resp.json()
                        raw_results = data.get("results", [])
                        source_records = []
                        for idx, r in enumerate(raw_results):
                            url = r.get("url", "")
                            if not is_valid_guidance_url(url, AUTHORITATIVE_DOMAINS):
                                continue

                            parsed = urlparse(url)
                            domain = (parsed.hostname or "").lower()

                            # Treat content as untrusted; truncate to 400 characters
                            content = r.get("content", "").strip()
                            clean_content = content[:400] if len(content) > 400 else content

                            rec = SourceRecord(
                                id=f"SRC-LIVE-{idx + 1:02d}",
                                url=url,
                                title=r.get("title", "Authoritative Guidance"),
                                domain=domain,
                                published_or_updated_at=None,
                                retrieved_at=retrieval_iso,
                                snippet=clean_content,
                                content_digest=sha256_digest(clean_content),
                                query=query,
                                source_mode="LIVE_RETRIEVAL",
                                excerpt_kind="VERBATIM",
                                verified_at=None,
                                verification_note="Live retrieval from allowlisted domain via Tavily Search API.",
                            )
                            source_records.append(rec)

                        if source_records:
                            receipt = {
                                "status": "LIVE_SUCCESS",
                                "provider": "Tavily",
                                "query": query,
                                "latency_ms": latency_ms,
                                "source_count": len(source_records),
                                "domains": list(set(s.domain for s in source_records)),
                                "is_live": True,
                                "failure_reason": None
                            }
                            return source_records, receipt
                    else:
                        failure_reason = f"Tavily HTTP {resp.status_code}: {resp.text[:200]}"
            except Exception as e:
                failure_reason = f"Tavily live search exception: {type(e).__name__} - {e}"
        else:
            failure_reason = "TAVILY_API_KEY is not configured or contains placeholder."

        # Explicit fallback to pre-vetted cached guidance with failure reason
        source_records = []
        for item in CACHED_AUTHORITATIVE_GUIDANCE[:max_results]:
            rec = SourceRecord(
                id=item["id"],
                url=item["url"],
                title=item["title"],
                domain=item["domain"],
                published_or_updated_at=item["published_or_updated_at"],
                retrieved_at=retrieval_iso,
                snippet=item["snippet"],
                content_digest=sha256_digest(item["snippet"]),
                query=query,
                source_mode=item["source_mode"],
                excerpt_kind=item["excerpt_kind"],
                verified_at=item["verified_at"],
                verification_note=item["verification_note"],
            )
            source_records.append(rec)

        latency_ms = int((time.time() - start_time) * 1000)
        receipt = {
            "status": "DEMO_FIXTURE_FALLBACK",
            "provider": "Tavily (Pre-Vetted Public Health Cache)",
            "query": query,
            "latency_ms": latency_ms,
            "source_count": len(source_records),
            "domains": list(set(s.domain for s in source_records)),
            "is_live": False,
            "failure_reason": failure_reason
        }
        return source_records, receipt

    async def search_guidance_async(
        self,
        query: str,
        max_results: int = 3,
        max_retries: int = 2
    ) -> tuple[list[SourceRecord], dict[str, Any]]:
        """Asynchronously queries Tavily Search API with strict schema, allowlist and bounded retries."""
        start_time = time.time()
        retrieval_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if self.has_key:
            tavily_payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "include_domains": AUTHORITATIVE_DOMAINS,
                "max_results": max_results
            }

            last_err = ""
            for attempt in range(max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post("https://api.tavily.com/search", json=tavily_payload)
                        latency_ms = int((time.time() - start_time) * 1000)

                        if resp.status_code == 200:
                            data = resp.json()
                            raw_results = data.get("results", [])
                            source_records = []
                            for idx, r in enumerate(raw_results):
                                url = r.get("url", "")
                                if not is_valid_guidance_url(url, AUTHORITATIVE_DOMAINS):
                                    continue

                                parsed = urlparse(url)
                                domain = (parsed.hostname or "").lower()

                                content = r.get("content", "").strip()
                                clean_content = content[:400] if len(content) > 400 else content

                                rec = SourceRecord(
                                    id=f"SRC-LIVE-{idx + 1:02d}",
                                    url=url,
                                    title=r.get("title", "Authoritative Guidance"),
                                    domain=domain,
                                    published_or_updated_at=None,
                                    retrieved_at=retrieval_iso,
                                    snippet=clean_content,
                                    content_digest=sha256_digest(clean_content),
                                    query=query,
                                    source_mode="LIVE_RETRIEVAL",
                                    excerpt_kind="VERBATIM",
                                    verified_at=None,
                                    verification_note="Live retrieval from allowlisted domain via Tavily Search API.",
                                )
                                source_records.append(rec)

                            if source_records:
                                receipt = {
                                    "status": "LIVE_SUCCESS",
                                    "provider": "Tavily",
                                    "query": query,
                                    "latency_ms": latency_ms,
                                    "source_count": len(source_records),
                                    "domains": list(set(s.domain for s in source_records)),
                                    "is_live": True,
                                    "failure_reason": None
                                }
                                return source_records, receipt
                        elif resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                            last_err = f"Tavily HTTP {resp.status_code}"
                            continue
                        else:
                            last_err = f"Tavily HTTP {resp.status_code}: {resp.text[:200]}"
                            break
                except Exception as e:
                    last_err = f"Tavily live search exception: {type(e).__name__} - {e}"
                    if attempt >= max_retries:
                        break

            failure_reason = last_err
        else:
            failure_reason = "TAVILY_API_KEY is not configured or contains placeholder."

        # Fallback to pre-vetted cached guidance
        source_records = []
        for item in CACHED_AUTHORITATIVE_GUIDANCE[:max_results]:
            rec = SourceRecord(
                id=item["id"],
                url=item["url"],
                title=item["title"],
                domain=item["domain"],
                published_or_updated_at=item["published_or_updated_at"],
                retrieved_at=retrieval_iso,
                snippet=item["snippet"],
                content_digest=sha256_digest(item["snippet"]),
                query=query,
                source_mode=item["source_mode"],
                excerpt_kind=item["excerpt_kind"],
                verified_at=item["verified_at"],
                verification_note=item["verification_note"],
            )
            source_records.append(rec)

        latency_ms = int((time.time() - start_time) * 1000)
        receipt = {
            "status": "DEMO_FIXTURE_FALLBACK",
            "provider": "Tavily (Pre-Vetted Public Health Cache)",
            "query": query,
            "latency_ms": latency_ms,
            "source_count": len(source_records),
            "domains": list(set(s.domain for s in source_records)),
            "is_live": False,
            "failure_reason": failure_reason
        }
        return source_records, receipt
