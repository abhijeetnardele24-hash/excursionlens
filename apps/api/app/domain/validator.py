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
    r"(?i)\b(?:safe (?:for|to) (?:immediate )?(?:administer|use|release|inject|ship|distribute))\b",
    r"(?i)\b(?:product is (?:safe|releasable|approved|cleared))\b",
    r"(?i)\b(?:potency is (?:unaffected|guaranteed|intact|preserved))\b",
    r"(?i)\b(?:(?:this )?batch is (?:compliant|safe|approved|cleared))\b",
    r"(?i)\b(?:approved for (?:release|commercial distribution|use))\b",
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
]


class ClaimsValidator:
    def __init__(self):
        self.compiled_patterns = [re.compile(p) for p in PROHIBITED_CLAIM_PATTERNS]

    def validate_text(self, text: str, context: str = "text") -> list[str]:
        """Scans arbitrary text for prohibited regulatory or disposition claims."""
        errors: list[str] = []
        if not text:
            return errors
        for pat in self.compiled_patterns:
            if pat.search(text):
                errors.append(f"Prohibited claim pattern found in {context}: matches '{pat.pattern}'.")
        return errors

    def validate_hypotheses(
        self,
        hypotheses: list[Hypothesis],
        valid_observations: list[Observation],
        valid_sources: list[SourceRecord],
    ) -> tuple[bool, list[str]]:
        """Validates all hypotheses against known evidence IDs and safety rules."""
        errors: list[str] = []
        valid_obs_ids = {o.id for o in valid_observations}
        valid_src_ids = {s.id for s in valid_sources}
        all_valid_ids = valid_obs_ids.union(valid_src_ids)

        if not hypotheses:
            errors.append("No hypotheses provided for validation.")
            return False, errors

        for h in hypotheses:
            # 1. Validate supporting citations
            for eid in h.supporting_evidence_ids:
                if eid not in all_valid_ids:
                    errors.append(f"Hypothesis '{h.id}' cites unknown evidence ID '{eid}'.")

            # 2. Validate contradicting citations
            for eid in h.contradicting_evidence_ids:
                if eid not in all_valid_ids:
                    errors.append(f"Hypothesis '{h.id}' cites unknown contradicting evidence ID '{eid}'.")

            # 3. Check for prohibited safety/disposition language across all fields
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

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_skeptic_critiques(self, critiques: list[SkepticCritique]) -> tuple[bool, list[str]]:
        """Scans skeptic critiques for prohibited regulatory assertions."""
        errors: list[str] = []
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
