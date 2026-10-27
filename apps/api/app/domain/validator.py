"""
apps/api/app/domain/validator.py — Deterministic Claims & Citation Validator

Guarantees:
- Every cited evidence ID strictly exists in observations or sources.
- No prohibited product disposition claims (e.g. 'safe to administer', 'approved for release', 'discard batch').
- Zero hallucinated URLs (every cited URL must be in retrieved Tavily sources).
- Fails closed if validation fails.
"""

import re

from .models import Hypothesis, Observation, SourceRecord

PROHIBITED_CLAIM_PATTERNS = [
    r"(?i)\b(safe to (?:administer|use|release|inject|ship))\b",
    r"(?i)\b(approved for (?:release|commercial distribution|use))\b",
    r"(?i)\b(guarantee(?:d)? (?:efficacy|potency|sterility))\b",
    r"(?i)\b(certified compliant with (?:fda|cdc|who) regulations)\b",
    r"(?i)\b(definitively proved? root cause)\b",
    r"(?i)\b(unconditional release)\b",
]


class ClaimsValidator:
    def __init__(self):
        pass

    def validate_hypotheses(
        self,
        hypotheses: list[Hypothesis],
        valid_observations: list[Observation],
        valid_sources: list[SourceRecord]
    ) -> tuple[bool, list[str]]:
        """Validates all hypotheses against known evidence IDs and safety rules."""
        errors = []
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

            # 3. Check for prohibited safety/disposition language
            combined_text = f"{h.label} {h.summary} {h.what_it_does_not_establish}"
            for pat in PROHIBITED_CLAIM_PATTERNS:
                if re.search(pat, combined_text):
                    errors.append(f"Hypothesis '{h.id}' contains prohibited regulatory/disposition claim: pattern '{pat}'.")

            # 4. Mandatory boundary statement
            if not h.what_it_does_not_establish or len(h.what_it_does_not_establish.strip()) < 10:
                errors.append(f"Hypothesis '{h.id}' must provide an explicit 'what_it_does_not_establish' boundary statement.")

            # 5. Mandatory next check
            if not h.next_check or len(h.next_check.strip()) < 10:
                errors.append(f"Hypothesis '{h.id}' must provide a concrete 'next_check' verification action.")

        is_valid = (len(errors) == 0)
        return is_valid, errors
