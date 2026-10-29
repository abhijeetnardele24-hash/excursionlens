"""
apps/api/tests/test_source_provenance.py - Regression Tests for Source Provenance, URLs & Evidence Truthfulness

Proves:
1. Fixture records are labeled VERIFIED_FIXTURE and PARAPHRASE with valid verification notes and dates.
2. Live results are labeled LIVE_RETRIEVAL and VERBATIM.
3. Suffix, userinfo, port, and non-HTTPS URL attacks remain strictly rejected.
4. Every committed fixture URL is a working official HTTPS endpoint.
5. Generated HTML reports never display paraphrased text as a quoted verbatim excerpt.
"""

import ssl
import urllib.request
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from apps.api.app.domain.models import (
    InvestigationRun,
    ProductProfile,
    ShipmentCase,
    ShipmentProfile,
    SourceRecord,
    TemperaturePolicy,
)
from apps.api.app.providers.tavily import (
    CACHED_AUTHORITATIVE_GUIDANCE,
    TavilySearchProvider,
    is_valid_guidance_url,
)
from apps.api.app.reports.generator import generate_printable_html_report
from scripts.live_smoke import is_valid_live_smoke_url


def test_fixture_records_provenance_labels():
    provider = TavilySearchProvider(api_key="", app_mode="live")
    sources, receipt = provider.search_guidance("temperature excursion", max_results=3)

    assert len(sources) > 0
    assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"

    for s in sources:
        assert s.source_mode == "VERIFIED_FIXTURE"
        assert s.excerpt_kind == "PARAPHRASE"
        assert s.verified_at is not None
        assert s.verification_note is not None
        assert "not a verbatim quotation" in s.verification_note.lower()


@pytest.mark.asyncio
async def test_live_results_provenance_labels():
    provider = TavilySearchProvider(api_key="mock-key-tavily-auth-testing", app_mode="live")
    mock_resp = {
        "results": [
            {
                "url": "https://www.cdc.gov/vaccines/hcp/storage-handling/",
                "title": "Live CDC Guidance",
                "content": "Live verbatim guidance snippet text from authoritative search."
            }
        ]
    }

    mock_post_resp = AsyncMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json = lambda: mock_resp

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_post_resp):
        sources, receipt = await provider.search_guidance_async("vaccine excursion", max_results=1)
        assert len(sources) == 1
        live_src = sources[0]
        assert live_src.source_mode == "LIVE_RETRIEVAL"
        assert live_src.excerpt_kind == "VERBATIM"
        assert live_src.verified_at is None
        assert receipt["status"] == "LIVE_SUCCESS"


@pytest.mark.parametrize(
    "attack_url",
    [
        "http://cdc.gov/vaccines",  # non-https
        "ftp://cdc.gov/file",  # non-https
        "https://evil.com@cdc.gov/vaccines",  # userinfo trick
        "https://user:pass@fda.gov/drugs",  # userinfo credentials
        "https://cdc.gov.attacker.com/toolkit",  # suffix lookalike
        "https://notfda.gov/guidance",  # prefix lookalike
        "https://cdc.gov:99999/test",  # invalid port
        "",  # empty
        "javascript:alert(1)",  # scheme injection
    ],
)
def test_url_attack_vectors_rejected(attack_url: str):
    assert is_valid_guidance_url(attack_url) is False
    assert is_valid_live_smoke_url(attack_url) is False


def test_committed_fixture_urls_are_valid_and_reachable():
    headers = {"User-Agent": "curl/8.4.0", "Accept": "*/*"}
    ctx = ssl.create_default_context()

    for item in CACHED_AUTHORITATIVE_GUIDANCE:
        url = item["url"]
        assert url.startswith("https://")
        assert is_valid_guidance_url(url) is True

        # Test reachability with timeout
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            assert resp.status == 200, f"Committed URL {url} returned HTTP {resp.status}"


def test_report_generator_never_quotes_paraphrased_fixture_snippet():
    case = ShipmentCase(
        id="CASE-TEST",
        title="Test Case",
        synthetic=True,
        created_at="2026-10-25T10:00:00Z",
        shipment=ShipmentProfile(
            shipment_id="TEST-01",
            origin="A",
            destination="B",
            carrier="C",
            transport_mode="TRUCK",
        ),
        product_profile=ProductProfile(
            product_name="P",
            product_class="C",
            lot_number="L1",
            dose_count=100,
        ),
        temperature_policy=TemperaturePolicy(
            min_celsius=2.0,
            max_celsius=8.0,
            max_allowed_excursion_minutes=0,
        ),
        readings=[{"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0}],
    )

    paraphrase_snippet = "This is a verified paraphrase summary of guidance."
    run = InvestigationRun(
        id="RUN-TEST",
        case_id="CASE-TEST",
        state="HUMAN_REVIEW_READY",
        created_at="2026-10-25T10:00:00Z",
        provider_mode="DEMO_FIXTURE",
        requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
        sources=[
            SourceRecord(
                id="SRC-TEST-01",
                url="https://www.cdc.gov/vaccines/hcp/storage-handling/",
                title="CDC Guidance",
                domain="cdc.gov",
                retrieved_at="2026-10-25T10:00:00Z",
                snippet=paraphrase_snippet,
                content_digest="hash123",
                query="test query",
                source_mode="VERIFIED_FIXTURE",
                excerpt_kind="PARAPHRASE",
                verified_at="2026-10-29",
                verification_note="Verified paraphrase summary",
            )
        ],
    )

    html = generate_printable_html_report(run, case)
    # Proves snippet is rendered without quotation marks around it
    assert f'"{paraphrase_snippet}"' not in html
    assert f'&quot;{paraphrase_snippet}&quot;' not in html
    assert paraphrase_snippet in html
    assert "VERIFIED FIXTURE" in html
    assert "Verified Paraphrase" in html

