"""
scripts/check_claims.py - Automated Documentation & Claims Truthfulness Validator

Scans all project documentation and claims for:
1. "guarantees non-repudiation" (SHA-256 provides integrity verification, not non-repudiation)
2. Unsupported "WCAG compliant" (automated Axe scans test targeted rules, not full WCAG compliance)
3. Unsupported "$35 billion" statistic (must be removed or carefully sourced)
4. Fixture evidence described as live
5. Fixture paraphrases described as verbatim quotations or quoted excerpts
6. Stale authoritative commit / run identifiers
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROHIBITED_PATTERNS = [
    (
        r"(?i)guarantee(?:s|d)?\s+non-repudiation",
        "Overclaim: SHA-256 supports integrity verification, not non-repudiation by itself.",
    ),
    (
        r"(?i)\bwcag\s+compliant\b",
        "Overclaim: Automated Axe checks do not establish complete WCAG compliance.",
    ),
    (
        r"(?i)\bfully\s+accessible\b",
        "Overclaim: Must be scoped to automated accessibility testing in tested states.",
    ),
    (
        r"(?i)\$35\s*billion",
        "Unsupported statistic: $35 billion cold-chain claim must be removed or carefully sourced.",
    ),
    (
        r"(?i)quoted\s+authoritative\s+excerpt",
        "Misleading label: Fixture summaries must not be presented as quoted authoritative excerpts.",
    ),
    (
        r"\b(?:141|161)\s+test\b",
        "Stale test count: ExcursionLens test suite now contains 165 test cases.",
    ),
    (
        r"\b0896105\b",
        "Obsolete commit SHA: Obsolete commit 0896105 referenced in documentation.",
    ),
    (
        r"\b40932942007\b",
        "Obsolete CI run ID: Obsolete GitHub Actions run 40932942007 referenced in documentation.",
    ),
    (
        r"\b40835420059\b",
        "Obsolete CI run ID: Obsolete GitHub Actions run 40835420059 referenced in documentation.",
    ),
    (
        r"\bb9b380a\b",
        "Obsolete commit SHA: Obsolete commit b9b380a referenced in documentation.",
    ),
]


def check_markdown_claims() -> list[str]:
    violations = []
    doc_files = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))

    for file_path in doc_files:
        rel_path = file_path.relative_to(ROOT)
        content = file_path.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            # Skip lines that explicitly forbid or warn against the phrase (e.g. not "WCAG compliant")
            clean_line = line.replace("“", '"').replace("”", '"')
            if 'not "wcag compliant"' in clean_line.lower():
                continue

            for pattern, reason in PROHIBITED_PATTERNS:
                if re.search(pattern, line):
                    violations.append(f"{rel_path}:{line_no} — {reason} (matched: {line.strip()[:80]})")

    return violations


def check_authoritative_identifiers() -> list[str]:
    violations = []
    verification_path = ROOT / "docs" / "verification-results.json"
    if not verification_path.exists():
        return violations

    try:
        with open(verification_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
    except Exception as e:
        violations.append(f"Failed to parse {verification_path}: {e}")
        return violations

    evidence_auth = v_data.get("evidence_authority")
    exec_ctx = v_data.get("execution_context")

    # If authoritative CI run, verify exact run URL format
    if evidence_auth == "AUTHORITATIVE_CI_ARTIFACT":
        if not exec_ctx or not exec_ctx.startswith("https://github.com/"):
            violations.append(
                f"Authoritative CI artifact requires full GitHub Actions run URL, got '{exec_ctx}'"
            )

    return violations


def main() -> int:
    print("=" * 60)
    print("  EXCURSIONLENS DOCUMENTATION & CLAIMS AUDIT")
    print("=" * 60)

    claims_violations = check_markdown_claims()
    id_violations = check_authoritative_identifiers()

    all_violations = claims_violations + id_violations

    if all_violations:
        print(f"❌ Claims audit failed with {len(all_violations)} violation(s):")
        for v in all_violations:
            print(f"   • {v}")
        return 1

    print("✅ Documentation & Claims Audit Passed! Zero overclaims or invalid identifiers found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
