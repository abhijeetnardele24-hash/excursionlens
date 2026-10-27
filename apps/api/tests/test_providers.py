"""
apps/api/tests/test_providers.py — Unit Tests for Provider Hardening and Report HTML Escaping
"""

from unittest.mock import patch

import httpx
import pytest
from apps.api.app.domain.models import InvestigationRun, Observation, ShipmentCase, SourceRecord
from apps.api.app.providers.nebius import NebiusTokenFactoryProvider
from apps.api.app.providers.tavily import AUTHORITATIVE_DOMAINS, TavilySearchProvider
from apps.api.app.reports.generator import generate_printable_html_report


def test_tavily_domain_allowlist_and_https_filtering():
    provider = TavilySearchProvider(api_key="", app_mode="demo")
    assert AUTHORITATIVE_DOMAINS == ["cdc.gov", "fda.gov", "who.int", "gs1.org"]

    # In fixture/demo mode without live key, it returns fallback sources with DEMO_FIXTURE status
    sources, receipt = provider.search_guidance("vaccine storage temperature excursion")
    assert len(sources) > 0
    assert receipt["status"] in ("DEMO_FIXTURE", "DEMO_FIXTURE_FALLBACK")
    for s in sources:
        assert any(d in s.domain for d in AUTHORITATIVE_DOMAINS)
        assert s.url.startswith("https://")
        assert len(s.content_digest) == 64  # SHA-256 hex


def test_nebius_fixture_fallback_labels():
    provider = NebiusTokenFactoryProvider(api_key="", app_mode="demo")
    assert provider.has_key is False

    case = ShipmentCase.model_validate({
        "id": "CASE-MIN",
        "title": "Minimal",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {"shipment_id": "MIN-1", "origin": "A", "destination": "B", "carrier": "C", "transport_mode": "TRUCK"},
        "product_profile": {"product_name": "P", "product_class": "Biologic", "lot_number": "L", "dose_count": 10},
        "temperature_policy": {"min_celsius": 2.0, "max_celsius": 8.0, "max_allowed_excursion_minutes": 0},
        "readings": [{"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0}],
        "custody_events": [],
        "operational_events": [],
    })

    hypotheses, receipt = provider.generate_hypotheses(case, [], [])
    assert len(hypotheses) >= 2
    assert receipt["status"] in ("DEMO_FIXTURE", "DEMO_FIXTURE_FALLBACK")
    assert receipt["is_live"] is False

    critiques, s_receipt = provider.run_skeptic_pass(hypotheses, [], [])
    assert len(critiques) >= 1
    assert s_receipt["status"] in ("DEMO_FIXTURE", "DEMO_FIXTURE_FALLBACK")
    assert s_receipt["is_live"] is False


def test_report_generator_escapes_xss_and_neutralizes_unsafe_schemes():
    run = InvestigationRun(
        id="RUN-XSS-TEST",
        case_id="CASE-XSS",
        state="HUMAN_REVIEW_READY",
        created_at="2026-10-25T10:00:00Z",
        provider_mode="DEMO_FIXTURE",
        requested_model="model",
        observations=[
            Observation(
                id="OBS-1",
                kind="EXCURSION_WINDOW",
                start_at="2026-10-25T10:00:00Z",
                end_at="2026-10-25T10:05:00Z",
                numeric_values={"duration_minutes": 5.0},
                unit="MINUTES",
                summary="<script>alert('xss_obs')</script>",
                source_event_ids=[],
                detector_version="1.0",
            )
        ],
        sources=[
            SourceRecord(
                id="SRC-1",
                url="javascript:alert('xss_link')",
                title="<img src=x onerror=alert('xss_img')>",
                domain="evil.com",
                retrieved_at="2026-10-25T10:00:00Z",
                snippet="<svg onload=alert('xss_svg')>",
                content_digest="abc",
                query="q",
            )
        ],
        hypotheses=[],
        critiques=[],
        tool_events=[],
    )

    case = ShipmentCase.model_validate({
        "id": "CASE-XSS",
        "title": "XSS Case",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {"shipment_id": "XSS-1", "origin": "A", "destination": "B", "carrier": "C", "transport_mode": "TRUCK"},
        "product_profile": {"product_name": "<script>alert('xss_product')</script>", "product_class": "Biologic", "lot_number": "L", "dose_count": 10},
        "temperature_policy": {"min_celsius": 2.0, "max_celsius": 8.0, "max_allowed_excursion_minutes": 0},
        "readings": [{"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0}],
        "custody_events": [],
        "operational_events": [],
    })

    html = generate_printable_html_report(run, case)

    # Prove raw unescaped script tags are NOT present
    assert "<script>alert('xss_obs')</script>" not in html
    assert "<script>alert('xss_product')</script>" not in html
    assert "<img src=x onerror=alert('xss_img')>" not in html
    assert "<svg onload=alert('xss_svg')>" not in html

    # Prove escaped representations are present
    assert "&lt;script&gt;alert(&#x27;xss_obs&#x27;)&lt;/script&gt;" in html or "&lt;script&gt;alert('xss_obs')&lt;/script&gt;" in html
    assert "&lt;img src=x onerror=alert(&#x27;xss_img&#x27;)&gt;" in html or "&lt;img src=x onerror=alert('xss_img')&gt;" in html

    # Prove javascript: link is replaced with safe #
    assert 'href="javascript:' not in html
    assert 'href="#"' in html


def test_report_generator_distinguishes_all_execution_states():
    case = ShipmentCase.model_validate({
        "id": "CASE-AUDIT",
        "title": "Audit Case",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {"shipment_id": "AUDIT-1", "origin": "A", "destination": "B", "carrier": "C", "transport_mode": "TRUCK"},
        "product_profile": {"product_name": "Vaccine", "product_class": "Biologic", "lot_number": "L1", "dose_count": 500},
        "temperature_policy": {"min_celsius": 2.0, "max_celsius": 8.0, "max_allowed_excursion_minutes": 0},
        "readings": [{"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0}],
        "custody_events": [],
        "operational_events": [],
    })

    # 1. LIVE_TOKEN_FACTORY
    run_live = InvestigationRun(
        id="RUN-LIVE",
        case_id="CASE-AUDIT",
        state="HUMAN_REVIEW_READY",
        created_at="2026-10-25T10:00:00Z",
        provider_mode="LIVE_TOKEN_FACTORY",
        requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
        served_model="nvidia/llama-3.1-nemotron-70b-instruct",
        response_digest="digest_live_123",
    )
    html_live = generate_printable_html_report(run_live, case)
    assert "Cryptographic Execution Audit (Fully Verified Live Token Factory Mode)" in html_live
    assert "nvidia/llama-3.1-nemotron-70b-instruct" in html_live

    # 2. DEMO_FIXTURE_FALLBACK
    run_fallback = InvestigationRun(
        id="RUN-FALLBACK",
        case_id="CASE-AUDIT",
        state="HUMAN_REVIEW_READY",
        created_at="2026-10-25T10:00:00Z",
        provider_mode="DEMO_FIXTURE_FALLBACK",
        requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
        failure_reason="Nebius rate limited (429)",
    )
    html_fallback = generate_printable_html_report(run_fallback, case)
    assert "Live Provider Request Attempted &bull; Fixture Fallback Engaged" in html_fallback
    assert "Nebius rate limited (429)" in html_fallback

    # 3. FAILED_TRUTHFULLY
    run_failed = InvestigationRun(
        id="RUN-FAILED",
        case_id="CASE-AUDIT",
        state="FAILED_TRUTHFULLY",
        created_at="2026-10-25T10:00:00Z",
        provider_mode="DEMO_FIXTURE",
        requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
        failure_reason="Claims validator detected prohibited claim pattern",
    )
    html_failed = generate_printable_html_report(run_failed, case)
    assert "Live Execution Terminated (Truthful Failure)" in html_failed
    assert "Claims validator detected prohibited claim pattern" in html_failed


@pytest.mark.asyncio
async def test_nebius_bounded_repair_success():
    """Tests that a malformed JSON first response is repaired by the bounded repair attempt."""
    provider = NebiusTokenFactoryProvider(api_key="valid-mock-key-12345", app_mode="live")
    assert provider.has_key is True

    case = ShipmentCase.model_validate({
        "id": "CASE-REPAIR",
        "title": "Repair Test",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {"shipment_id": "REP-1", "origin": "A", "destination": "B", "carrier": "C", "transport_mode": "TRUCK"},
        "product_profile": {"product_name": "P", "product_class": "Biologic", "lot_number": "L", "dose_count": 10},
        "temperature_policy": {"min_celsius": 2.0, "max_celsius": 8.0, "max_allowed_excursion_minutes": 0},
        "readings": [{"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0}],
        "custody_events": [],
        "operational_events": [],
    })

    # Response 1: malformed JSON; Response 2 (repair): valid JSON
    mock_bad_resp = httpx.Response(200, json={
        "choices": [{"message": {"content": "INVALID JSON {{not closed"}}],
        "usage": {"total_tokens": 50}
    }, request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"))

    mock_repaired_resp = httpx.Response(200, json={
        "choices": [{
            "message": {
                "content": '{"hypotheses": [{"id": "HYP-01", "label": "Door Open Exposure", "summary": "Warm air entered during door opening.", "supporting_evidence_ids": ["OBS-01"], "contradicting_evidence_ids": [], "unknowns": ["Door gasket seal"], "next_check": "Inspect door sensor", "confidence_band": "HIGH", "status": "LEADING", "what_it_does_not_establish": "Does not prove potency loss."}]}'
            }
        }],
        "usage": {"total_tokens": 120}
    }, request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"))

    with patch("httpx.AsyncClient.post", side_effect=[mock_bad_resp, mock_repaired_resp]):
        hypotheses, receipt = await provider.generate_hypotheses_async(case, [], [])
        assert len(hypotheses) == 1
        assert hypotheses[0].id == "HYP-01"
        assert receipt["status"] == "LIVE_SUCCESS"
        assert receipt["is_live"] is True


@pytest.mark.asyncio
async def test_nebius_bounded_repair_failure_falls_back_truthfully():
    """Tests that when repair also fails, provider falls back truthfully without claiming live."""
    provider = NebiusTokenFactoryProvider(api_key="valid-mock-key-12345", app_mode="live")

    case = ShipmentCase.model_validate({
        "id": "CASE-REPAIR-FAIL",
        "title": "Repair Fail Test",
        "synthetic": True,
        "created_at": "2026-10-25T10:00:00Z",
        "shipment": {"shipment_id": "REP-2", "origin": "A", "destination": "B", "carrier": "C", "transport_mode": "TRUCK"},
        "product_profile": {"product_name": "P", "product_class": "Biologic", "lot_number": "L", "dose_count": 10},
        "temperature_policy": {"min_celsius": 2.0, "max_celsius": 8.0, "max_allowed_excursion_minutes": 0},
        "readings": [{"timestamp": "2026-10-25T10:00:00Z", "temperature_celsius": 4.0}],
        "custody_events": [],
        "operational_events": [],
    })

    # Both initial and repair calls fail
    mock_bad_resp1 = httpx.Response(200, json={
        "choices": [{"message": {"content": "MALFORMED 1"}}],
        "usage": {"total_tokens": 50}
    }, request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"))

    mock_bad_resp2 = httpx.Response(500, text="Internal Error", request=httpx.Request("POST", "https://api.tokenfactory.nebius.com/v1/chat/completions"))

    with patch("httpx.AsyncClient.post", side_effect=[mock_bad_resp1, mock_bad_resp2]):
        hypotheses, receipt = await provider.generate_hypotheses_async(case, [], [])
        assert len(hypotheses) >= 2  # Fixture fallback
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"
        assert receipt["is_live"] is False
        assert "failed after bounded repair" in receipt["failure_reason"]


@pytest.mark.asyncio
async def test_tavily_live_search_success_and_filtering():
    """Tests live Tavily search parsing and domain allowlist enforcement."""
    provider = TavilySearchProvider(api_key="tvly-mock-key-12345", app_mode="live")
    assert provider.has_key is True

    mock_resp = httpx.Response(200, json={
        "results": [
            {
                "url": "https://www.cdc.gov/vaccines/storage/guidelines.html",
                "title": "CDC Cold Chain Storage Guidelines",
                "content": "Maintain vaccine storage temperatures between 2 and 8 degrees Celsius."
            },
            {
                "url": "https://untrusted-blog.com/vaccines",
                "title": "Untrusted Blog",
                "content": "Random opinions on storage."
            }
        ]
    }, request=httpx.Request("POST", "https://api.tavily.com/search"))

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        sources, receipt = await provider.search_guidance_async("CDC vaccine guidelines")
        assert len(sources) == 1
        assert "cdc.gov" in sources[0].domain
        assert receipt["status"] == "LIVE_SUCCESS"
        assert receipt["is_live"] is True

