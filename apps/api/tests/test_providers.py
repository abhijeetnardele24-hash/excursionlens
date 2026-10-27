"""
apps/api/tests/test_providers.py — Unit Tests for Provider Hardening and Report HTML Escaping
"""

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
