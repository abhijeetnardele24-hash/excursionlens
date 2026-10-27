"""
apps/api/app/domain/validator.py — Deterministic Claims & Citation Validator

Guarantees:
- Every cited evidence ID strictly exists in observations or sources.
- No prohibited product disposition claims (e.g. 'safe to administer', 'approved for release', 'potency is unaffected', 'discard this shipment').
- Rejects unsupported regulatory certifications ('21 CFR Part 11 compliant', 'mandatory quarantine in effect').
- Inspects every generated field: labels, summaries, unknowns, next checks, skeptic critiques, counterfactuals, and report text.
- Fails closed if validation fails.
"""

import re
from typing import Any

from .models import CounterfactualResult, Hypothesis, Observation, SkepticCritique, SourceRecord

PROHIBITED_CLAIM_PATTERNS = [
    r"(?i)\b(?:safe (?:for|to) (?:immediate )?(?:administer|use|release|inject|ship|distribute|commercial use))\b",
    r"(?i)\b(?:product is (?:safe|releasable|approved|cleared|usable|potent))\b",
    r"(?i)\b(?:potency is (?:unaffected|guaranteed|intact|preserved|maintained))\b",
    r"(?i)\b(?:(?:this )?batch is (?:compliant|safe|approved|cleared))\b",
    r"(?i)\b(?:approved for (?:release|commercial distribution|use|clinical use))\b",
    r"(?i)\b(?:product release is approved)\b",
    r"(?i)\b(?:guarantee(?:d)? (?:efficacy|potency|sterility|safety))\b",
    r"(?i)\b(?:(?:certified |confirms |proven |asserts )?compliant with (?:fda|cdc|who)(?: regulations)?)\b",
    r"(?i)\b(?:(?:fda|cdc|who) compliance)\b",
    r"(?i)\b(?:21\s*cfr\s*part\s*11\s*compliant)\b",
    r"(?i)\b(?:mandatory quarantine is in effect)\b",
    r"(?i)\b(?:unconditional release)\b",
    r"(?i)\b(?:definitively proved? root cause)\b",
    r"(?i)\b(?:discard this shipment)\b",
    r"(?i)\b(?:destroy (?:this|the) (?:batch|shipment|product|inventory))\b",
    r"(?i)\b(?:authoritative disposition determination|final product disposition|disposition determination is made)\b",
    r"(?i)\b(?:final regulatory determination|authoritative regulatory determination|binding regulatory determination|official regulatory determination)\b",
    r"(?i)\b(?:constitutes (?:a )?regulatory determination)\b",
    r"(?i)\b(?:legally cleared(?:\s+for)?)\b",
]

UNSUPPORTED_CAUSAL_CERTAINTY_PATTERNS = [
    r"(?i)\b(?:definitely caused by|conclusively proves?|100%\s*(?:certain(?:ty)?|proven)|indisputable proof|unquestionable root cause|irrefutable proof|sole and certain cause|without a doubt caused by|proves beyond doubt)\b",
]

PROHIBITED_TEMP_UNIT_PATTERNS = [
    r"(?i)\b(?:\d+(?:\.\d+)?)\s*(?:°\s*F|deg(?:rees?)?\s*F|fahrenheit)\b",
]


class ClaimsValidator:
    def __init__(self):
        self.prohibited_patterns = [re.compile(p) for p in PROHIBITED_CLAIM_PATTERNS]
        self.causal_certainty_patterns = [re.compile(p) for p in UNSUPPORTED_CAUSAL_CERTAINTY_PATTERNS]
        self.unit_patterns = [re.compile(p) for p in PROHIBITED_TEMP_UNIT_PATTERNS]

    def validate_text(self, text: str, context: str = "text") -> list[str]:
        """Scans arbitrary text for prohibited regulatory, disposition, or certainty claims."""
        errors: list[str] = []
        if not text:
            return errors
        for pat in self.prohibited_patterns:
            if pat.search(text):
                errors.append(f"Prohibited claim pattern found in {context}: matches '{pat.pattern}'.")
        for pat in self.causal_certainty_patterns:
            if pat.search(text):
                errors.append(f"Unsupported causal certainty found in {context}: matches '{pat.pattern}'.")
        for pat in self.unit_patterns:
            m = pat.search(text)
            if m:
                errors.append(f"Prohibited temperature unit (Fahrenheit) found in {context}: '{m.group(0)}'. Telemetry is strictly Celsius.")
        return errors

    def validate_hypotheses(
        self,
        hypotheses: list[Hypothesis],
        valid_observations: list[Observation],
        valid_sources: list[SourceRecord],
    ) -> tuple[bool, list[str]]:
        """Validates all hypotheses against known evidence IDs, numerical consistency, and safety rules."""
        errors: list[str] = []
        obs_map = {o.id: o for o in valid_observations}
        src_map = {s.id: s for s in valid_sources}
        all_valid_ids = set(obs_map.keys()).union(set(src_map.keys()))

        if not hypotheses:
            errors.append("No hypotheses provided for validation.")
            return False, errors

        for h in hypotheses:
            # 1. Validate supporting citations
            if not h.supporting_evidence_ids:
                errors.append(f"Hypothesis '{h.id}' must cite at least one valid supporting evidence ID.")
            for eid in h.supporting_evidence_ids:
                if eid not in all_valid_ids:
                    errors.append(f"Hypothesis '{h.id}' cites unknown evidence ID '{eid}'.")

            # 2. Validate contradicting citations
            for eid in h.contradicting_evidence_ids:
                if eid not in all_valid_ids:
                    errors.append(f"Hypothesis '{h.id}' cites unknown contradicting evidence ID '{eid}'.")

            # 3. Check for prohibited safety/disposition language & causal certainty across all fields
            text_blocks = [
                (h.label, f"Hypothesis '{h.id}' label"),
                (h.summary, f"Hypothesis '{h.id}' summary"),
                (h.what_it_does_not_establish, f"Hypothesis '{h.id}' boundary"),
                (h.next_check, f"Hypothesis '{h.id}' next check"),
            ]
            for u in h.unknowns:
                text_blocks.append((u, f"Hypothesis '{h.id}' unknown"))

            for text, ctx in text_blocks:
                errors.extend(self.validate_text(text, ctx))

            # 4. Mandatory boundary statement
            if not h.what_it_does_not_establish or len(h.what_it_does_not_establish.strip()) < 10:
                errors.append(f"Hypothesis '{h.id}' must provide an explicit 'what_it_does_not_establish' boundary statement.")

            # 5. Mandatory next check
            if not h.next_check or len(h.next_check.strip()) < 10:
                errors.append(f"Hypothesis '{h.id}' must provide a concrete 'next_check' verification action.")

            # 6. Mandatory unknowns to prevent uncalibrated certainty
            if not h.unknowns:
                errors.append(f"Hypothesis '{h.id}' must list at least one unknown to represent epistemic limits.")

            # 7. Numerical statement consistency against cited observations
            combined_hypothesis_text = f"{h.label} {h.summary}"
            cited_obs = [obs_map[eid] for eid in h.supporting_evidence_ids if eid in obs_map]

            if cited_obs:
                # Check peak/excursion temperature claims against cited observation maximums
                peak_matches = re.finditer(
                    r"(?i)\b(?:peak(?:ed)?\s+(?:at\s+)?|surface\s+temperature\s+(?:to\s+peak\s+at\s+)?|excursion\s+(?:temperature\s+)?(?:reached\s+)?|temperature\s+reached\s+)(\d+(?:\.\d+)?)\s*(?:°\s*C|deg(?:rees?)?\s*C|celsius)",
                    combined_hypothesis_text,
                )
                for pm in peak_matches:
                    claimed_val = float(pm.group(1))
                    observed_peaks = [
                        obs.numeric_values[k]
                        for obs in cited_obs
                        for k in ["max_temperature", "max_celsius"]
                        if k in obs.numeric_values
                    ]
                    if observed_peaks:
                        max_obs_peak = max(observed_peaks)
                        min_obs_peak = min(observed_peaks)
                        if claimed_val > max_obs_peak + 2.0 or claimed_val < min_obs_peak - 2.0:
                            errors.append(
                                f"Hypothesis '{h.id}' claims peak/excursion temperature {claimed_val}°C, which contradicts cited observation "
                                f"(recorded maximum {max_obs_peak:.1f}°C across cited observations)."
                            )

                # Check duration claims against cited observations
                dur_matches = re.finditer(
                    r"(?i)\b(?:excursion\s+duration\s+(?:of\s+)?|excursion\s+(?:lasted\s+)?(?:for\s+)?|duration\s+of\s+)(\d+(?:\.\d+)?)\s*(?:minutes|mins)\b",
                    combined_hypothesis_text,
                )
                for dm in dur_matches:
                    claimed_dur = float(dm.group(1))
                    observed_durs = [
                        obs.numeric_values[k]
                        for obs in cited_obs
                        for k in ["duration_minutes", "total_excursion_minutes"]
                        if k in obs.numeric_values
                    ]
                    if observed_durs:
                        max_dur = max(observed_durs)
                        if claimed_dur > max_dur * 1.5 and (claimed_dur - max_dur) > 10.0:
                            errors.append(
                                f"Hypothesis '{h.id}' claims excursion duration {claimed_dur} minutes, which contradicts cited observation duration "
                                f"(maximum recorded {max_dur:.1f} minutes across cited observations)."
                            )

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_skeptic_critiques(
        self,
        critiques: list[SkepticCritique],
        hypotheses: list[Hypothesis] | None = None
    ) -> tuple[bool, list[str]]:
        """Scans skeptic critiques for prohibited assertions, validity of targeted hypothesis IDs, and coverage."""
        errors: list[str] = []

        if hypotheses:
            hyp_ids = {h.id for h in hypotheses}
            critiqued_ids = {c.hypothesis_id for c in critiques}

            # 1. Every critique must reference an existing hypothesis
            for c in critiques:
                if c.hypothesis_id not in hyp_ids:
                    errors.append(f"Critique targets non-existent hypothesis ID '{c.hypothesis_id}'.")

            # 2. Every hypothesis must receive skeptic coverage
            uncovered = hyp_ids - critiqued_ids
            if uncovered:
                errors.append(f"Skeptic review failed to provide coverage for hypotheses: {sorted(uncovered)}.")

        for c in critiques:
            errors.extend(self.validate_text(c.attack_summary, f"Critique for '{c.hypothesis_id}' attack summary"))
            errors.extend(self.validate_text(c.rationale, f"Critique for '{c.hypothesis_id}' rationale"))
            for claim in c.unsupported_claims:
                errors.extend(self.validate_text(claim, f"Critique for '{c.hypothesis_id}' unsupported claim"))
            for cont in c.ignored_contradictions:
                errors.extend(self.validate_text(cont, f"Critique for '{c.hypothesis_id}' contradiction"))
        return len(errors) == 0, errors

    def validate_counterfactual(self, cf: CounterfactualResult) -> tuple[bool, list[str]]:
        """Validates counterfactual summary and limits for prohibited claims."""
        errors: list[str] = []
        errors.extend(self.validate_text(cf.result_summary, "Counterfactual result summary"))
        errors.extend(self.validate_text(cf.limits, "Counterfactual limits"))
        return len(errors) == 0, errors

    def inspect_complete_run(self, run_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Deep scan across complete investigation run object."""
        errors: list[str] = []
        for h in run_data.get("hypotheses", []):
            errors.extend(self.validate_text(h.get("summary", ""), f"Hypothesis {h.get('id')} summary"))
            errors.extend(self.validate_text(h.get("what_it_does_not_establish", ""), f"Hypothesis {h.get('id')} boundary"))
        for c in run_data.get("critiques", []):
            errors.extend(self.validate_text(c.get("rationale", ""), "Critique rationale"))
        if "counterfactual" in run_data and run_data["counterfactual"]:
            errors.extend(self.validate_text(run_data["counterfactual"].get("result_summary", ""), "Counterfactual summary"))
        return len(errors) == 0, errors


DeterministicClaimsValidator = ClaimsValidator
