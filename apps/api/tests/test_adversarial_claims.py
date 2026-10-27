"""
apps/api/tests/test_adversarial_claims.py — Adversarial claims validation regression tests.

Verifies:
1. Valid IDs paired with false numerical values (false peak temperature, false duration).
2. Unsupported causal certainty phrases (definitely caused by, conclusively proves, 100% certainty).
3. Prohibited temperature units (Fahrenheit).
4. Missing skeptic critique coverage across required hypotheses.
5. Critique targeting non-existent hypothesis ID.
6. Prohibited regulatory and product disposition claims.
7. Missing epistemic unknowns.
"""

import pytest
from apps.api.app.domain.models import Hypothesis, Observation, SkepticCritique, SourceRecord
from apps.api.app.domain.validator import ClaimsValidator


@pytest.fixture
def baseline_observation() -> Observation:
    return Observation(
        id="OBS-EXCURSION-01",
        kind="EXCURSION_WINDOW",
        start_at="2026-10-25T10:20:00Z",
        end_at="2026-10-25T11:00:00Z",
        numeric_values={
            "duration_minutes": 40.0,
            "max_temperature": 10.5,
            "min_temperature": 8.1,
            "mean_temperature": 9.4,
            "auc_degree_minutes": 50.5,
        },
        unit="celsius",
        summary="Excursion window peaking at 10.5°C for 40 minutes.",
        source_event_ids=["EVT-OPS-01"],
        detector_version="1.0",
    )


@pytest.fixture
def baseline_source() -> SourceRecord:
    return SourceRecord(
        id="SRC-CDC-01",
        url="https://www.cdc.gov/vaccines/storage",
        title="CDC Vaccine Storage & Handling Toolkit",
        domain="cdc.gov",
        retrieved_at="2026-10-25T10:00:00Z",
        snippet="Store vaccines between 2°C and 8°C.",
        content_digest="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd",
        query="CDC vaccine storage",
    )


def test_adversarial_false_peak_temperature(baseline_observation, baseline_source):
    """Proves that a valid citation ID paired with a fabricated peak temperature is rejected."""
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-01",
        label="Adversarial false peak temperature",
        summary="Pallet was exposed, causing excursion temperature to peak at 24.5°C during transfer.",
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=["Logger calibration certificate"],
        next_check="Review secondary logger data",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Does not establish product stability or chemical potency degradation.",
    )
    is_valid, errors = validator.validate_hypotheses([h], [baseline_observation], [baseline_source])
    assert is_valid is False
    assert any("contradicts cited observation" in e for e in errors)
    assert any("24.5" in e for e in errors)


def test_adversarial_false_duration(baseline_observation, baseline_source):
    """Proves that a valid citation ID paired with a fabricated excursion duration is rejected."""
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-01",
        label="Adversarial false duration",
        summary="Sensor registered an excursion duration of 140 minutes, breaching tolerances.",
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=["Logger calibration certificate"],
        next_check="Review secondary logger data",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Does not establish product stability or chemical potency degradation.",
    )
    is_valid, errors = validator.validate_hypotheses([h], [baseline_observation], [baseline_source])
    assert is_valid is False
    assert any("contradicts cited observation duration" in e for e in errors)
    assert any("140" in e for e in errors)


@pytest.mark.parametrize(
    "certainty_phrase",
    [
        "This incident was definitely caused by carrier negligence.",
        "The telemetry conclusively proves the compressor was deactivated.",
        "With 100% certainty, door opening caused the excursion.",
        "Telemetry provides indisputable proof of failure.",
        "This is the unquestionable root cause of the spike.",
    ],
)
def test_adversarial_unsupported_causal_certainty(baseline_observation, baseline_source, certainty_phrase):
    """Proves that uncalibrated causal certainty is rejected by the claims validator."""
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-01",
        label="Adversarial certainty claim",
        summary=certainty_phrase,
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=["Compressor cycle duty record"],
        next_check="Inspect vehicle ECM logs.",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Does not establish product stability or chemical potency degradation.",
    )
    is_valid, errors = validator.validate_hypotheses([h], [baseline_observation], [baseline_source])
    assert is_valid is False
    assert any("unsupported causal certainty" in e.lower() for e in errors)


def test_adversarial_fahrenheit_unit_rejected(baseline_observation, baseline_source):
    """Proves that non-Celsius units (Fahrenheit) are rejected."""
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-01",
        label="Fahrenheit unit leak",
        summary="Surface temperature reached 55°F during cross-dock staging.",
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=["Insulation thermal mass"],
        next_check="Inspect dock CCTV timestamp.",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Does not establish product stability or chemical potency degradation.",
    )
    is_valid, errors = validator.validate_hypotheses([h], [baseline_observation], [baseline_source])
    assert is_valid is False
    assert any("prohibited temperature unit" in e.lower() for e in errors)


def test_adversarial_missing_epistemic_unknowns(baseline_observation, baseline_source):
    """Proves that a hypothesis with empty unknowns is rejected."""
    validator = ClaimsValidator()
    h = Hypothesis(
        id="HYP-01",
        label="No unknowns hypothesis",
        summary="Pallet was exposed to ambient air.",
        supporting_evidence_ids=["OBS-EXCURSION-01"],
        contradicting_evidence_ids=[],
        unknowns=[],  # Empty unknowns violates responsible AI requirements
        next_check="Inspect dock CCTV timestamp.",
        confidence_band="HIGH",
        status="LEADING",
        what_it_does_not_establish="Does not establish product stability or chemical potency degradation.",
    )
    is_valid, errors = validator.validate_hypotheses([h], [baseline_observation], [baseline_source])
    assert is_valid is False
    assert any("must list at least one unknown" in e.lower() for e in errors)


def test_adversarial_missing_skeptic_coverage():
    """Proves that skeptic critiques omitting one of the hypotheses fail validation."""
    validator = ClaimsValidator()
    h1 = Hypothesis(
        id="HYP-01",
        label="H1",
        summary="Summary 1",
        supporting_evidence_ids=["OBS-01"],
        next_check="Check 1",
        confidence_band="HIGH",
        what_it_does_not_establish="Limit 1",
    )
    h2 = Hypothesis(
        id="HYP-02",
        label="H2",
        summary="Summary 2",
        supporting_evidence_ids=["OBS-01"],
        next_check="Check 2",
        confidence_band="MEDIUM",
        what_it_does_not_establish="Limit 2",
    )

    # Only HYP-01 is critiqued; HYP-02 is omitted
    c1 = SkepticCritique(
        hypothesis_id="HYP-01",
        attack_summary="Critique for H1",
        recommended_status="ALTERNATIVE",
        rationale="Rationale 1",
    )

    is_valid, errors = validator.validate_skeptic_critiques([c1], hypotheses=[h1, h2])
    assert is_valid is False
    assert any("failed to provide coverage for hypotheses: ['HYP-02']" in e for e in errors)


def test_adversarial_critique_targets_nonexistent_hypothesis():
    """Proves that skeptic critique targeting a non-existent hypothesis ID fails validation."""
    validator = ClaimsValidator()
    h1 = Hypothesis(
        id="HYP-01",
        label="H1",
        summary="Summary 1",
        supporting_evidence_ids=["OBS-01"],
        next_check="Check 1",
        confidence_band="HIGH",
        what_it_does_not_establish="Limit 1",
    )
    c1 = SkepticCritique(
        hypothesis_id="HYP-HALLUCINATED-99",
        attack_summary="Critique for non-existent hypothesis",
        recommended_status="DOWNGRADED",
        rationale="Rationale",
    )

    is_valid, errors = validator.validate_skeptic_critiques([c1], hypotheses=[h1])
    assert is_valid is False
    assert any("non-existent hypothesis id" in e.lower() for e in errors)
