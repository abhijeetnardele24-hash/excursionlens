"""
apps/api/tests/test_live_classification_failclose.py — Regression tests proving fail-closed live classification.

Verifies the 9 mandatory Section 2A invariants:
1. Invalid Nebius key never appears live
2. Missing Tavily key never appears live
3. Empty model catalog never appears live
4. Catalog without NVIDIA/Nemotron models never appears live
5. Model not present in the catalog never appears live
6. Investigator-only success never appears fully live
7. Skeptic-only failure prevents live mode
8. Partial provider success is represented truthfully as DEMO_FIXTURE_FALLBACK
9. Complete verified success is the only path to LIVE_TOKEN_FACTORY
"""

from unittest.mock import AsyncMock

import pytest
from apps.api.app.agent.state_machine import InvestigationOrchestrator
from apps.api.app.domain.models import (
    Hypothesis,
    ProductProfile,
    SensorReading,
    ShipmentCase,
    ShipmentProfile,
    SkepticCritique,
    SourceRecord,
    TemperaturePolicy,
)


@pytest.fixture
def minimal_case() -> ShipmentCase:
    return ShipmentCase(
        id="CASE-TEST-01",
        title="Test Incident",
        synthetic=True,
        created_at="2026-10-25T10:00:00Z",
        shipment=ShipmentProfile(
            shipment_id="TEST-01",
            origin="Hub A",
            destination="Hub B",
            carrier="ColdFleet",
            transport_mode="REFRIGERATED_TRUCK",
        ),
        product_profile=ProductProfile(
            product_name="Biologic Vaccine",
            product_class="Vaccine",
            lot_number="LOT-001",
            dose_count=1000,
        ),
        temperature_policy=TemperaturePolicy(
            min_celsius=2.0,
            max_celsius=8.0,
            max_allowed_excursion_minutes=0,
        ),
        readings=[
            SensorReading(timestamp="2026-10-25T10:00:00Z", temperature_celsius=5.0, sensor_id="PRIMARY"),
            SensorReading(timestamp="2026-10-25T10:10:00Z", temperature_celsius=10.5, sensor_id="PRIMARY"),
            SensorReading(timestamp="2026-10-25T10:20:00Z", temperature_celsius=5.0, sensor_id="PRIMARY"),
        ],
    )


@pytest.fixture
def valid_mock_hypotheses() -> list[Hypothesis]:
    return [
        Hypothesis(
            id="HYP-01",
            label="Ambient intrusion",
            summary="Surface temperature reached 10.5°C during transfer door opening.",
            supporting_evidence_ids=["OBS-EXCURSION-01", "SRC-CDC-01"],
            contradicting_evidence_ids=[],
            unknowns=["Dock seal integrity log"],
            next_check="Inspect physical receiving inspection photos.",
            confidence_band="HIGH",
            status="LEADING",
            what_it_does_not_establish="Does not determine product safety, potency, or regulatory release.",
        )
    ]


@pytest.fixture
def valid_mock_critiques() -> list[SkepticCritique]:
    return [
        SkepticCritique(
            hypothesis_id="HYP-01",
            attack_summary="Hypothesis requires verification of secondary core sensor.",
            unsupported_claims=[],
            ignored_contradictions=[],
            recommended_status="LEADING",
            rationale="Consistent with recorded door opening interval.",
        )
    ]


@pytest.fixture
def valid_mock_sources() -> list[SourceRecord]:
    return [
        SourceRecord(
            id="SRC-CDC-01",
            url="https://www.cdc.gov/vaccines/storage",
            title="CDC Vaccine Storage & Handling Toolkit",
            domain="cdc.gov",
            retrieved_at="2026-10-25T10:05:00Z",
            snippet="Cold-chain products must remain within 2.0C to 8.0C.",
            content_digest="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd",
            query="CDC vaccine storage",
        )
    ]


@pytest.mark.asyncio
async def test_invalid_nebius_key_never_live(minimal_case):
    """Scenario 1: When Nebius key is invalid or missing, run must never be LIVE_TOKEN_FACTORY."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = False
    orch.tavily.has_key = True

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.state in ("HUMAN_REVIEW_READY", "FAILED_TRUTHFULLY")
    assert run.provider_mode != "LIVE_TOKEN_FACTORY"
    assert run.provider_mode == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_missing_tavily_key_never_live(minimal_case):
    """Scenario 2: When Tavily key is missing, run must never be LIVE_TOKEN_FACTORY."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = False

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.provider_mode != "LIVE_TOKEN_FACTORY"
    assert run.provider_mode == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_empty_model_catalog_never_live(minimal_case, valid_mock_hypotheses, valid_mock_critiques, valid_mock_sources):
    """Scenario 3: Empty model catalog from GET /models must fail closed and never allow LIVE_TOKEN_FACTORY."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = True

    orch.nebius.discover_models_async = AsyncMock(return_value={
        "status": "LIVE_SUCCESS",
        "nvidia_models": [],
        "selected_deep_model": None,
    })
    orch.tavily.search_guidance_async = AsyncMock(return_value=(valid_mock_sources, {"is_live": True, "status": "LIVE_SUCCESS"}))
    orch.nebius.generate_hypotheses_async = AsyncMock(return_value=(valid_mock_hypotheses, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": "nvidia/llama-3.1-nemotron-70b-instruct", "response_digest": "dig123"
    }))
    orch.nebius.run_skeptic_pass_async = AsyncMock(return_value=(valid_mock_critiques, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": "nvidia/llama-3.1-nemotron-70b-instruct", "response_digest": "dig456"
    }))

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.provider_mode != "LIVE_TOKEN_FACTORY"
    assert run.provider_mode == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_catalog_without_nvidia_models_never_live(minimal_case, valid_mock_hypotheses, valid_mock_critiques, valid_mock_sources):
    """Scenario 4: Catalog without eligible NVIDIA/Nemotron models must never appear live."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = True

    orch.nebius.discover_models_async = AsyncMock(return_value={
        "status": "LIVE_SUCCESS",
        "nvidia_models": [],
        "all_models": ["some-generic-model-7b"],
        "selected_deep_model": None,
    })
    orch.tavily.search_guidance_async = AsyncMock(return_value=(valid_mock_sources, {"is_live": True, "status": "LIVE_SUCCESS"}))
    orch.nebius.generate_hypotheses_async = AsyncMock(return_value=(valid_mock_hypotheses, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": "some-generic-model-7b", "response_digest": "dig123"
    }))
    orch.nebius.run_skeptic_pass_async = AsyncMock(return_value=(valid_mock_critiques, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": "some-generic-model-7b", "response_digest": "dig456"
    }))

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.provider_mode != "LIVE_TOKEN_FACTORY"
    assert run.provider_mode == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_model_not_present_in_catalog_never_live(minimal_case, valid_mock_hypotheses, valid_mock_critiques, valid_mock_sources):
    """Scenario 5: When served model is absent from the returned catalog, live mode is blocked."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = True

    orch.nebius.discover_models_async = AsyncMock(return_value={
        "status": "LIVE_SUCCESS",
        "nvidia_models": ["nvidia/nemotron-4-340b-instruct"],
        "selected_deep_model": "nvidia/nemotron-4-340b-instruct",
    })
    orch.tavily.search_guidance_async = AsyncMock(return_value=(valid_mock_sources, {"is_live": True, "status": "LIVE_SUCCESS"}))
    # Served model is different and absent from the catalog
    orch.nebius.generate_hypotheses_async = AsyncMock(return_value=(valid_mock_hypotheses, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": "nvidia/unlisted-nemotron-model", "response_digest": "dig123"
    }))
    orch.nebius.run_skeptic_pass_async = AsyncMock(return_value=(valid_mock_critiques, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": "nvidia/unlisted-nemotron-model", "response_digest": "dig456"
    }))

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.provider_mode != "LIVE_TOKEN_FACTORY"
    assert run.provider_mode == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_investigator_only_success_never_fully_live(minimal_case, valid_mock_hypotheses, valid_mock_critiques, valid_mock_sources):
    """Scenario 6: Investigator success paired with non-live skeptic must never appear fully live."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = True

    model_name = "nvidia/llama-3.1-nemotron-70b-instruct"
    orch.nebius.discover_models_async = AsyncMock(return_value={
        "status": "LIVE_SUCCESS",
        "nvidia_models": [model_name],
        "selected_deep_model": model_name,
    })
    orch.tavily.search_guidance_async = AsyncMock(return_value=(valid_mock_sources, {"is_live": True, "status": "LIVE_SUCCESS"}))
    # Investigator succeeded live
    orch.nebius.generate_hypotheses_async = AsyncMock(return_value=(valid_mock_hypotheses, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": model_name, "response_digest": "dig123"
    }))
    # Skeptic fell back to fixture
    orch.nebius.run_skeptic_pass_async = AsyncMock(return_value=(valid_mock_critiques, {
        "is_live": False, "status": "DEMO_FIXTURE_FALLBACK", "model": model_name, "failure_reason": "Skeptic rate limited"
    }))

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.provider_mode != "LIVE_TOKEN_FACTORY"
    assert run.provider_mode == "DEMO_FIXTURE_FALLBACK"


@pytest.mark.asyncio
async def test_skeptic_only_failure_prevents_live_mode(minimal_case, valid_mock_hypotheses, valid_mock_sources):
    """Scenario 7: Skeptic-only failure prevents live classification."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = True

    model_name = "nvidia/llama-3.1-nemotron-70b-instruct"
    orch.nebius.discover_models_async = AsyncMock(return_value={
        "status": "LIVE_SUCCESS",
        "nvidia_models": [model_name],
        "selected_deep_model": model_name,
    })
    orch.tavily.search_guidance_async = AsyncMock(return_value=(valid_mock_sources, {"is_live": True, "status": "LIVE_SUCCESS"}))
    orch.nebius.generate_hypotheses_async = AsyncMock(return_value=(valid_mock_hypotheses, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": model_name, "response_digest": "dig123"
    }))
    orch.nebius.run_skeptic_pass_async = AsyncMock(return_value=([], {
        "is_live": False, "status": "FAILED", "model": model_name, "failure_reason": "Nebius HTTP 500"
    }))

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.provider_mode != "LIVE_TOKEN_FACTORY"


@pytest.mark.asyncio
async def test_partial_provider_success_represented_truthfully(minimal_case):
    """Scenario 8: Partial provider success is labeled DEMO_FIXTURE_FALLBACK, never silent promotion."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = False  # Tavily missing

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.provider_mode == "DEMO_FIXTURE_FALLBACK"
    assert "fallback" in (run.served_model or "").lower()


@pytest.mark.asyncio
async def test_complete_verified_success_is_only_path_to_live_token_factory(
    minimal_case, valid_mock_hypotheses, valid_mock_critiques, valid_mock_sources
):
    """Scenario 9: Only complete verified end-to-end execution achieves LIVE_TOKEN_FACTORY."""
    orch = InvestigationOrchestrator()
    orch.nebius.has_key = True
    orch.tavily.has_key = True

    model_name = "nvidia/llama-3.1-nemotron-70b-instruct"
    orch.nebius.discover_models_async = AsyncMock(return_value={
        "status": "LIVE_SUCCESS",
        "nvidia_models": [model_name],
        "selected_deep_model": model_name,
    })
    orch.tavily.search_guidance_async = AsyncMock(return_value=(valid_mock_sources, {
        "is_live": True, "status": "LIVE_SUCCESS"
    }))
    orch.nebius.generate_hypotheses_async = AsyncMock(return_value=(valid_mock_hypotheses, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": model_name, "response_digest": "inv_sha256_digest_verified"
    }))
    orch.nebius.run_skeptic_pass_async = AsyncMock(return_value=(valid_mock_critiques, {
        "is_live": True, "status": "LIVE_SUCCESS", "model": model_name, "response_digest": "skep_sha256_digest_verified"
    }))

    rid = orch.start_investigation(minimal_case)
    run = await orch.wait_for_completion(rid)

    assert run.state == "HUMAN_REVIEW_READY"
    assert run.provider_mode == "LIVE_TOKEN_FACTORY"
    assert run.served_model == model_name
    assert run.validation_result is not None
    assert run.validation_result["passed"] is True
