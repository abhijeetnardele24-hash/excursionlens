"""
apps/api/tests/test_claims_validator.py — Regression Tests for ClaimsValidator Prohibited Patterns
"""

import pytest
from apps.api.app.domain.models import Hypothesis, Observation, SourceRecord
from apps.api.app.domain.validator import ClaimsValidator


@pytest.fixture
def base_obs() -> list[Observation]:
    return [
        Observation(
            id="OBS-EXCURSION-01",
            kind="EXCURSION_WINDOW",
            start_at="2026-10-25T10:25:00Z",
            end_at="2026-10-25T11:05:00Z",
            numeric_values={"duration_minutes": 40.0, "max_temperature": 10.5},
            unit="MINUTES",
            summary="Continuous excursion",
            source_event_ids=["EVT-OPS-01"],
            detector_version="1.0",
        )
    ]


@pytest.fixture
def base_sources() -> list[SourceRecord]:
    return [
        SourceRecord(
            id="SRC-CDC-01",
            url="https://www.cdc.gov/vaccines/storage",
            title="CDC Vaccine Storage",
            domain="cdc.gov",
            retrieved_at="2026-10-25T10:00:00Z",
            snippet="Keep between 2 and 8C.",
            content_digest="abc123hash",
            query="test",
        )
    ]


def test_validator_accepts_valid_hypothesis(base_obs, base_sources):
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-01",
        label="Cross-dock exposure",
        summary="Pallet was exposed to ambient temperatures during cross-dock staging.",
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=["Refrigeration unit setpoint log"],
        next_check="Check reefer compressor download",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Does not establish product stability or chemical potency degradation.",
    )
    passed, errors = validator.validate_hypotheses([h], base_obs, base_sources)
    assert passed is True
    assert len(errors) == 0


@pytest.mark.parametrize(
    "prohibited_claim",
    [
        "The product is safe for immediate release.",
        "This batch is compliant with regulations.",
        "Potency is unaffected by the 40 min excursion.",
        "Discard this shipment immediately.",
        "This automated review is 21 CFR Part 11 compliant.",
        "Mandatory quarantine is in effect per CDC authority.",
        "This confirms FDA compliance for the lot.",
        "Product release is approved.",
    ],
)
def test_validator_rejects_regulatory_overclaims(base_obs, base_sources, prohibited_claim):
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-02",
        label="Compromised claim",
        summary=f"Analysis concluded: {prohibited_claim}",
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=[],
        next_check="Inspect manifest",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Limitations note.",
    )
    passed, errors = validator.validate_hypotheses([h], base_obs, base_sources)
    assert passed is False
    assert any("prohibited claim pattern" in err.lower() for err in errors)


def test_validator_rejects_unobserved_evidence_id(base_obs, base_sources):
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-03",
        label="Hallucinated evidence reference",
        summary="Valid summary.",
        supporting_evidence_ids=["OBS-NONEXISTENT-99"],
        contradicting_evidence_ids=[],
        unknowns=[],
        next_check="Inspect manifest",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Limitations note.",
    )
    passed, errors = validator.validate_hypotheses([h], base_obs, base_sources)
    assert passed is False
    assert any("cites unknown evidence id" in err.lower() for err in errors)
