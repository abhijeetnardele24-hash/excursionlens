"""
apps/api/tests/test_provider_deep_coverage.py — Deep Provider Mock Tests for Errors, Retries & Fallbacks
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from apps.api.app.domain.models import Observation, ShipmentCase
from apps.api.app.providers.nebius import NebiusTokenFactoryProvider
from apps.api.app.providers.tavily import TavilySearchProvider


@pytest.fixture
def sample_case():
    return ShipmentCase.model_validate({
        "id": "CASE-TEST-PROVIDER",
        "title": "Provider Deep Test Case",
        "synthetic": True,
        "created_at": "2026-10-21T10:00:00Z",
        "shipment": {"shipment_id": "SHP-01", "origin": "A", "destination": "B", "carrier": "C", "transport_mode": "TRUCK"},
        "product_profile": {"product_name": "Pentavalent", "product_class": "Biologic", "lot_number": "L88", "dose_count": 500},
        "temperature_policy": {"min_celsius": 2.0, "max_celsius": 8.0, "max_allowed_excursion_minutes": 0},
        "readings": [{"timestamp": "2026-10-21T10:15:00Z", "temperature_celsius": 10.5}],
        "custody_events": [],
        "operational_events": []
    })


@pytest.fixture
def sample_obs():
    return [
        Observation(
            id="OBS-EXCURSION-01",
            kind="EXCURSION_WINDOW",
            start_at="2026-10-21T10:15:00Z",
            end_at="2026-10-21T10:55:00Z",
            numeric_values={"duration_minutes": 40.0, "peak_celsius": 10.5, "auc": 50.5},
            unit="CELSIUS",
            summary="Breach above 8.0 C detected",
            source_event_ids=["EVT-01"],
            detector_version="1.0"
        )
    ]


# ==============================================================================
# Tavily Search Provider Deep Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_tavily_async_http_errors_fallback():
    provider = TavilySearchProvider(api_key="tvly-mock-key-12345", app_mode="live")

    # 1. 401 Unauthorized
    mock_resp_401 = MagicMock()
    mock_resp_401.status_code = 401
    mock_resp_401.text = "Unauthorized API key"
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp_401):
        sources, receipt = await provider.search_guidance_async("temperature excursion")
        assert len(sources) > 0  # Fell back to fixture sources
        assert any("cdc.gov" in s.domain for s in sources)
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"

    # 2. 429 Rate Limit
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.text = "Rate limit reached"
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp_429):
        sources, receipt = await provider.search_guidance_async("temperature excursion")
        assert len(sources) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"

    # 3. Timeout exception
    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.TimeoutException("Read timed out")):
        sources, receipt = await provider.search_guidance_async("temperature excursion")
        assert len(sources) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"

    # 4. Network error exception
    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.NetworkError("Connection refused")):
        sources, receipt = await provider.search_guidance_async("temperature excursion")
        assert len(sources) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_tavily_async_domain_filtering():
    provider = TavilySearchProvider(api_key="tvly-mock-key-12345", app_mode="live")

    # Mock response containing one allowlisted domain and one unallowlisted domain
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "url": "https://www.cdc.gov/vaccines/storage-guide.html",
                "title": "CDC Vaccine Storage Guide",
                "content": "Store vaccines between 2 and 8 C to maintain potency.",
            },
            {
                "url": "https://random-untrusted-blog.com/tips.html",
                "title": "Random Blog",
                "content": "Unverified claims.",
            }
        ]
    }
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=mock_resp):
        sources, receipt = await provider.search_guidance_async("vaccine storage")
        assert len(sources) == 1
        assert sources[0].domain == "www.cdc.gov"
        assert receipt["status"] == "LIVE_SUCCESS"


def test_tavily_probe_connectivity_cases():
    # 1. Missing key
    p_no_key = TavilySearchProvider(api_key="", app_mode="live")
    probe_no_key = p_no_key.probe_connectivity()
    assert probe_no_key["status"] == "NOT_CONFIGURED"

    # 2. Key present, success
    p_key = TavilySearchProvider(api_key="tvly-real-mock-12345", app_mode="live")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"url": "https://www.cdc.gov/guide"}]}
    with patch.object(httpx.Client, "post", return_value=mock_resp):
        probe_ok = p_key.probe_connectivity()
        assert probe_ok["status"] == "LIVE_SUCCESS"

    # 3. Key present, 401 error
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.text = "Invalid API key"
    with patch.object(httpx.Client, "post", return_value=mock_401):
        probe_fail = p_key.probe_connectivity()
        assert probe_fail["status"] == "FAILED"


# ==============================================================================
# Nebius Token Factory Deep Tests: Errors & Bounded Repair
# ==============================================================================

@pytest.mark.asyncio
async def test_nebius_hypothesis_generation_errors_and_fallback(sample_case, sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")

    # 1. 401 Unauthorized
    resp_401 = MagicMock()
    resp_401.status_code = 401
    resp_401.text = "Unauthorized"
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=resp_401):
        hypotheses, receipt = await provider.generate_hypotheses_async(sample_case, sample_obs, [])
        assert len(hypotheses) == 3
        assert receipt["is_live"] is False

    # 2. 500 Server Error
    resp_500 = MagicMock()
    resp_500.status_code = 500
    resp_500.text = "Internal Server Error"
    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock, return_value=resp_500):
        hypotheses, receipt = await provider.generate_hypotheses_async(sample_case, sample_obs, [])
        assert len(hypotheses) == 3
        assert receipt["is_live"] is False

    # 3. Timeout exception
    with patch.object(httpx.AsyncClient, "post", side_effect=httpx.TimeoutException("Timeout")):
        hypotheses, receipt = await provider.generate_hypotheses_async(sample_case, sample_obs, [])
        assert len(hypotheses) == 3
        assert receipt["is_live"] is False


@pytest.mark.asyncio
async def test_nebius_hypothesis_repair_protocol_success(sample_case, sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")

    # First call returns malformed non-JSON
    bad_resp = MagicMock()
    bad_resp.status_code = 200
    bad_resp.json.return_value = {
        "choices": [{"message": {"content": "I am not JSON at all!"}}]
    }

    # Second repair call returns valid JSON
    valid_repaired_json = """{
        "hypotheses": [
            {
                "id": "HYP-REPAIRED-01",
                "label": "Repaired Cross-Dock Staging Exposure",
                "summary": "Ambient heat infiltrated cargo door during cross-dock staging.",
                "supporting_evidence_ids": ["OBS-EXCURSION-01"],
                "contradicting_evidence_ids": [],
                "unknowns": ["Door seal degradation level"],
                "next_check": "Inspect dock staging logs",
                "confidence_band": "HIGH",
                "status": "LEADING",
                "what_it_does_not_establish": "Does not prove reefer compressor failure"
            }
        ]
    }"""
    repair_resp = MagicMock()
    repair_resp.status_code = 200
    repair_resp.json.return_value = {
        "choices": [{"message": {"content": valid_repaired_json}}]
    }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [bad_resp, repair_resp]
        hypotheses, receipt = await provider.generate_hypotheses_async(sample_case, sample_obs, [])
        assert len(hypotheses) == 1
        assert hypotheses[0].id == "HYP-REPAIRED-01"
        assert receipt["is_live"] is True
        assert mock_post.call_count == 2  # Proves 1 repair retry occurred


@pytest.mark.asyncio
async def test_nebius_hypothesis_repair_protocol_failed_fallback(sample_case, sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")

    # Both initial and repair calls return bad output
    bad_resp1 = MagicMock()
    bad_resp1.status_code = 200
    bad_resp1.json.return_value = {"choices": [{"message": {"content": "Bad response 1"}}]}

    bad_resp2 = MagicMock()
    bad_resp2.status_code = 200
    bad_resp2.json.return_value = {"choices": [{"message": {"content": "Still bad response 2"}}]}

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [bad_resp1, bad_resp2]
        hypotheses, receipt = await provider.generate_hypotheses_async(sample_case, sample_obs, [])
        assert len(hypotheses) == 3  # Fell back truthfully
        assert receipt["is_live"] is False
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_nebius_skeptic_repair_protocol_success(sample_case, sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")
    hypotheses, _ = provider.generate_hypotheses(sample_case, sample_obs, [])

    # First skeptic call returns non-JSON
    bad_resp = MagicMock()
    bad_resp.status_code = 200
    bad_resp.json.return_value = {"choices": [{"message": {"content": "Invalid skeptic text"}}]}

    # Second repair call returns valid critique JSON
    valid_skeptic_json = """{
        "critiques": [
            {
                "hypothesis_id": "HYP-01",
                "attack_summary": "Reefer bus voltage remained steady at 12.8V.",
                "unsupported_claims": [],
                "ignored_contradictions": [],
                "recommended_status": "LEADING",
                "rationale": "Consistent with physical sensor telemetry."
            }
        ]
    }"""
    repair_resp = MagicMock()
    repair_resp.status_code = 200
    repair_resp.json.return_value = {"choices": [{"message": {"content": valid_skeptic_json}}] }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [bad_resp, repair_resp]
        critiques, receipt = await provider.run_skeptic_pass_async(hypotheses, sample_obs, [])
        assert len(critiques) == 1
        assert critiques[0].hypothesis_id == "HYP-01"
        assert receipt["is_live"] is True
        assert mock_post.call_count == 2


def test_nebius_catalog_discovery_errors():
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")

    # 1. 500 error
    resp_500 = MagicMock()
    resp_500.status_code = 500
    with patch.object(httpx.Client, "get", return_value=resp_500):
        result = provider.discover_models()
        assert result["status"] == "FAILED"

    # 2. Empty models list
    resp_empty = MagicMock()
    resp_empty.status_code = 200
    resp_empty.json.return_value = {"data": []}
    with patch.object(httpx.Client, "get", return_value=resp_empty):
        result = provider.discover_models()
        assert result["status"] == "FAILED"
        assert result["error_category"] == "NO_NVIDIA_MODELS"


@pytest.mark.asyncio
async def test_nebius_catalog_discovery_async():
    # 1. No key
    p_no_key = NebiusTokenFactoryProvider(api_key="", app_mode="live")
    res_no_key = await p_no_key.discover_models_async()
    assert res_no_key["status"] == "NOT_CONFIGURED"

    # 2. Success with async client
    p_key = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "nvidia/llama-3.1-nemotron-70b-instruct"},
            {"id": "nvidia/nemotron-mini-4b-instruct"}
        ]
    }
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
        res_ok = await p_key.discover_models_async()
        assert res_ok["status"] == "LIVE_SUCCESS"
        assert len(res_ok["nvidia_models"]) == 2

    # 3. HTTP 401 error
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.text = "Invalid API key"
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_401):
        res_fail = await p_key.discover_models_async()
        assert res_fail["status"] == "FAILED"


def test_nebius_catalog_model_selection_regex_fallbacks():
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")
    # Configured model names are different, but catalog contains generic 70b and 8b
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "nvidia/other-70b-model"},
            {"id": "nvidia/other-8b-model"}
        ]
    }
    with patch.object(httpx.Client, "get", return_value=mock_resp):
        res = provider.discover_models()
        assert res["status"] == "LIVE_SUCCESS"
        assert res["selected_deep_model"] == "nvidia/other-70b-model"
        assert res["selected_fast_model"] == "nvidia/other-8b-model"


def test_tavily_sync_search_guidance():
    # 1. Without key in live mode -> falls back to fixture
    p_no_key = TavilySearchProvider(api_key="", app_mode="live")
    sources, receipt = p_no_key.search_guidance("temperature excursion")
    assert len(sources) > 0
    assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"

    # 2. With key, HTTP 200 success with scheme/domain filtering
    p_key = TavilySearchProvider(api_key="tvly-mock-key-12345", app_mode="live")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "url": "http://insecure-http.cdc.gov/test",
                "title": "Insecure HTTP",
                "content": "Not HTTPS."
            },
            {
                "url": "https://untrusted-domain.com/test",
                "title": "Untrusted Domain",
                "content": "Not allowlisted."
            },
            {
                "url": "https://www.cdc.gov/vaccines/guidelines.html",
                "title": "CDC Storage Guidelines",
                "content": "Maintain cold chain strictly between 2C and 8C."
            }
        ]
    }
    with patch.object(httpx.Client, "post", return_value=mock_resp):
        sources, receipt = p_key.search_guidance("vaccine cold chain")
        assert len(sources) == 1
        assert sources[0].domain == "www.cdc.gov"
        assert receipt["status"] == "LIVE_SUCCESS"

    # 3. HTTP 500 error
    mock_500 = MagicMock()
    mock_500.status_code = 500
    mock_500.text = "Internal Server Error"
    with patch.object(httpx.Client, "post", return_value=mock_500):
        sources, receipt = p_key.search_guidance("vaccine cold chain")
        assert len(sources) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"

    # 4. Exception
    with patch.object(httpx.Client, "post", side_effect=httpx.NetworkError("Refused")):
        sources, receipt = p_key.search_guidance("vaccine cold chain")
        assert len(sources) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"



def test_nebius_sync_skeptic_pass(sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")
    from apps.api.app.domain.models import Hypothesis
    hypotheses = [
        Hypothesis(
            id="HYP-01",
            label="REFRIGERATION_FAILURE",
            summary="Compressor power cut.",
            confidence=0.8,
            confidence_band="HIGH",
            next_check="Inspect compressor logs.",
            what_it_does_not_establish="Does not establish sensor failure.",
            status="LEADING",
            supporting_evidence_ids=["OBS-EXCURSION-01"],
            contradicting_evidence_ids=[],
            generation_model="nvidia/llama-3.1-nemotron-70b-instruct",
            provider_receipt={"status": "DEMO_FIXTURE"},
        )
    ]


    # Live call success
    valid_skeptic_json = """{
        "critiques": [
            {
                "hypothesis_id": "HYP-01",
                "attack_summary": "Reefer bus telemetry was stable.",
                "unsupported_claims": [],
                "ignored_contradictions": [],
                "recommended_status": "ALTERNATIVE",
                "rationale": "Stable voltage."
            }
        ]
    }"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": valid_skeptic_json}}]}
    with patch.object(httpx.Client, "post", return_value=mock_resp):
        critiques, receipt = provider.run_skeptic_pass(hypotheses, sample_obs, [])
        assert len(critiques) == 1
        assert receipt["is_live"] is True


def test_nebius_sync_generate_hypotheses_live_success_and_exception(sample_case, sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")
    valid_hypotheses_json = """{
        "hypotheses": [
            {
                "id": "HYP-01",
                "label": "Ambient intrusion",
                "summary": "Transfer door opening.",
                "supporting_evidence_ids": ["OBS-EXCURSION-01"],
                "contradicting_evidence_ids": [],
                "unknowns": [],
                "next_check": "Check logs.",
                "confidence_band": "HIGH",
                "status": "LEADING",
                "what_it_does_not_establish": "No safety claim."
            }
        ]
    }"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": valid_hypotheses_json}}], "usage": {}}
    with patch.object(httpx.Client, "post", return_value=mock_resp):
        hypotheses, receipt = provider.generate_hypotheses(sample_case, sample_obs, [])
        assert len(hypotheses) == 1
        assert receipt["status"] == "LIVE_SUCCESS"
        assert receipt["is_live"] is True

    # Exception fallback branch
    with patch.object(httpx.Client, "post", side_effect=httpx.NetworkError("Connection refused")):
        hypotheses, receipt = provider.generate_hypotheses(sample_case, sample_obs, [])
        assert len(hypotheses) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"
        assert "Connection refused" in receipt["failure_reason"]


def test_nebius_sync_skeptic_pass_fallback_and_exception(sample_obs):
    from apps.api.app.domain.models import Hypothesis
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")
    hypotheses = [
        Hypothesis(
            id="HYP-01",
            label="REFRIGERATION_FAILURE",
            summary="Compressor power cut.",
            confidence=0.8,
            confidence_band="HIGH",
            next_check="Inspect compressor logs.",
            what_it_does_not_establish="Does not establish sensor failure.",
            status="LEADING",
            supporting_evidence_ids=["OBS-EXCURSION-01"],
            contradicting_evidence_ids=[],
            generation_model="nvidia/llama-3.1-nemotron-70b-instruct",
            provider_receipt={"status": "DEMO_FIXTURE"},
        )
    ]

    # HTTP 500 fallback
    mock_500 = MagicMock()
    mock_500.status_code = 500
    mock_500.text = "Internal Server Error"
    with patch.object(httpx.Client, "post", return_value=mock_500):
        critiques, receipt = provider.run_skeptic_pass(hypotheses, sample_obs, [])
        assert len(critiques) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"

    # Network exception fallback
    with patch.object(httpx.Client, "post", side_effect=httpx.NetworkError("Socket closed")):
        critiques, receipt = provider.run_skeptic_pass(hypotheses, sample_obs, [])
        assert len(critiques) > 0
        assert receipt["status"] == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_nebius_async_hypotheses_retry_429(sample_case, sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")

    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.text = "Rate limited"

    valid_json = """{
        "hypotheses": [
            {
                "id": "HYP-01",
                "label": "Ambient intrusion",
                "summary": "Transfer door opening.",
                "supporting_evidence_ids": ["OBS-EXCURSION-01"],
                "contradicting_evidence_ids": [],
                "unknowns": [],
                "next_check": "Check logs.",
                "confidence_band": "HIGH",
                "status": "LEADING",
                "what_it_does_not_establish": "No safety claim."
            }
        ]
    }"""
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"choices": [{"message": {"content": valid_json}}], "usage": {}}

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [mock_429, mock_200]
        hypotheses, receipt = await provider.generate_hypotheses_async(sample_case, sample_obs, [])
        assert len(hypotheses) == 1
        assert receipt["status"] == "LIVE_SUCCESS"
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_nebius_async_skeptic_retry_503(sample_case, sample_obs):
    provider = NebiusTokenFactoryProvider(api_key="real-nebius-key-12345", app_mode="live")
    hypotheses, _ = provider.generate_hypotheses(sample_case, sample_obs, [])

    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.text = "Service Unavailable"

    valid_skeptic = """{
        "critiques": [
            {
                "hypothesis_id": "HYP-01",
                "attack_summary": "Reefer bus telemetry was stable.",
                "unsupported_claims": [],
                "ignored_contradictions": [],
                "recommended_status": "ALTERNATIVE",
                "rationale": "Stable voltage."
            }
        ]
    }"""
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"choices": [{"message": {"content": valid_skeptic}}], "usage": {}}

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [mock_503, mock_200]
        critiques, receipt = await provider.run_skeptic_pass_async(hypotheses, sample_obs, [])
        assert len(critiques) == 1
        assert receipt["status"] == "LIVE_SUCCESS"
        assert mock_post.call_count == 2


def test_reports_generator_edge_cases(sample_case):
    from apps.api.app.domain.models import InvestigationRun
    from apps.api.app.reports.generator import _esc, _get_git_commit_sha, _safe_url, generate_printable_html_report

    assert _esc(None) == ""
    assert _esc("safe & clean") == "safe &amp; clean"

    assert _safe_url("javascript:alert(1)") == "#"
    assert _safe_url("data:text/html,bad") == "#"
    assert _safe_url("") == "#"
    assert "https://example.com" in _safe_url("https://example.com/test")

    with patch.dict("os.environ", {"GITHUB_SHA": "abc123sha"}):
        assert _get_git_commit_sha() == "abc123sha"

    # Test report with REQUEST_ADDITIONAL_EVIDENCE posture
    run = InvestigationRun(
        id="RUN-POSTURE-TEST",
        case_id=sample_case.id,
        state="HUMAN_REVIEW_READY",
        created_at="2026-10-21T10:00:00Z",
        provider_mode="DEMO_FIXTURE",
        requested_model="nvidia/llama-3.1-nemotron-70b-instruct",
        observations=[],
        sources=[],
        hypotheses=[],
        critiques=[],
        review_posture="REQUEST_ADDITIONAL_EVIDENCE",
        tool_events=[],
        disclaimer="Test",
    )
    html = generate_printable_html_report(run, sample_case)
    assert "RUN-POSTURE-TEST" in html
    assert "Synthetic Fixture Investigator" in html


