"""
scripts/check_claims.py - Automated Documentation & Claims Truthfulness Validator

Scans all project documentation and claims for:
1. "guarantees non-repudiation" (SHA-256 provides integrity verification, not non-repudiation)
2. Unsupported "WCAG compliant" (automated Axe scans test targeted rules, not full WCAG compliance)
3. Unsupported "$35 billion" statistic (must be removed or carefully sourced)
4. Fixture evidence described as live
5. Fixture paraphrases described as verbatim quotations or quoted excerpts
6. Stale authoritative commit / run identifiers
7. Stale or mismatched test counts and coverage metrics vs test-results/coverage.json
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

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
    (
        r"(?i)\b93\.43%",
        "Stale statement coverage metric: Documented 93.43% must match authoritative Linux CI metric (92.98%).",
    ),
    (
        r"(?i)\b82\.43%",
        "Stale branch coverage metric: Documented 82.43% must match authoritative Linux CI metric (81.85%).",
    ),
    (
        r"(?i)\b90\.71%",
        "Stale combined coverage metric: Documented 90.71% must match authoritative Linux CI metric (90.24%).",
    ),
    (
        r"\b1,?478\s*(?:/|\b)",
        "Stale covered statement count: Documented 1,478 statements must match authoritative Linux CI count (1,471).",
    ),
    (
        r"\b427\s*/\s*518\b",
        "Stale covered branch count: Documented 427/518 branches must match authoritative Linux CI count (424/518).",
    ),
]


def check_markdown_claims(doc_files: list[Path] | None = None) -> list[str]:
    violations = []
    if doc_files is None:
        doc_files = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))

    for file_path in doc_files:
        rel_path = file_path.relative_to(ROOT) if file_path.is_relative_to(ROOT) else file_path.name
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


def check_authoritative_identifiers(verification_path: Path | None = None) -> list[str]:
    violations = []
    if verification_path is None:
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


def check_receipt_provenance(docs_dir: Path | None = None) -> list[str]:
    violations = []
    if docs_dir is None:
        docs_dir = ROOT / "docs"

    deploy_path = docs_dir / "deployment-receipt.json"
    if deploy_path.exists():
        try:
            with open(deploy_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            for req_key in ("evaluated_source_sha", "receipt_commit_sha", "evidence_authority", "execution_context", "status"):
                if req_key not in d:
                    violations.append(f"deployment-receipt.json missing required provenance field '{req_key}'")
            eval_sha = d.get("evaluated_source_sha", "")
            if eval_sha and len(eval_sha) != 40:
                violations.append(f"deployment-receipt.json: evaluated_source_sha must be 40-char SHA, got '{eval_sha}'")
            if d.get("status") == "LIVE_DEPLOYED":
                endpoint_commit = d.get("endpoint_commit")
                if endpoint_commit and endpoint_commit != eval_sha:
                    violations.append(
                        f"deployment-receipt.json: endpoint_commit '{endpoint_commit}' does not match evaluated_source_sha '{eval_sha}'"
                    )
        except Exception as e:
            violations.append(f"Failed to validate deployment-receipt.json provenance: {e}")

    smoke_path = docs_dir / "live-smoke-receipt.json"
    if smoke_path.exists():
        try:
            with open(smoke_path, "r", encoding="utf-8") as f:
                s = json.load(f)
            for req_key in ("evaluated_source_sha", "receipt_commit_sha", "evidence_authority", "execution_context", "status"):
                if req_key not in s:
                    violations.append(f"live-smoke-receipt.json missing required provenance field '{req_key}'")
            eval_sha = s.get("evaluated_source_sha", "")
            if eval_sha and len(eval_sha) != 40:
                violations.append(f"live-smoke-receipt.json: evaluated_source_sha must be 40-char SHA, got '{eval_sha}'")
            status = s.get("status")
            nebius_smoke = s.get("nebius_smoke", {})
            if status == "BLOCKED":
                if nebius_smoke.get("tested_model") is not None:
                    violations.append(
                        f"live-smoke-receipt.json: status is BLOCKED but tested_model is '{nebius_smoke.get('tested_model')}' (must be null)"
                    )
                if nebius_smoke.get("total_tokens") is not None:
                    violations.append(
                        f"live-smoke-receipt.json: status is BLOCKED but total_tokens is '{nebius_smoke.get('total_tokens')}' (must be null)"
                    )
                if s.get("provider_mode") not in ("DEMO_FIXTURE", "NOT_CONFIGURED"):
                    violations.append(
                        f"live-smoke-receipt.json: status is BLOCKED but provider_mode is '{s.get('provider_mode')}' (must be DEMO_FIXTURE)"
                    )
        except Exception as e:
            violations.append(f"Failed to validate live-smoke-receipt.json provenance: {e}")

    vr_path = docs_dir / "verification-results.json"
    if vr_path.exists():
        try:
            with open(vr_path, "r", encoding="utf-8") as f:
                vr = json.load(f)
            head_sha = vr.get("git", {}).get("head", "")
            if head_sha and len(head_sha) != 40:
                violations.append(f"verification-results.json: git.head must be 40-char SHA, got '{head_sha}'")
            ext_live = vr.get("external_gates", {}).get("live_providers", {})
            if ext_live.get("status") == "BLOCKED" and ext_live.get("served_nvidia_model") is not None:
                violations.append(
                    f"verification-results.json: live_providers is BLOCKED but served_nvidia_model is '{ext_live.get('served_nvidia_model')}' (must be null)"
                )
        except Exception as e:
            violations.append(f"Failed to validate verification-results.json provenance: {e}")

    return violations


def parse_coverage_totals(cov_data: dict[str, Any]) -> dict[str, Any]:
    totals = cov_data.get("totals", {})
    num_stmts = totals.get("num_statements", 0)
    covered_stmts = totals.get("covered_lines", totals.get("covered_statements", 0))
    stmt_pct = round((covered_stmts / num_stmts * 100.0), 2) if num_stmts else 0.0

    num_branches = totals.get("num_branches", 0)
    covered_branches = totals.get("covered_branches", 0)
    branch_pct = round((covered_branches / num_branches * 100.0), 2) if num_branches else 0.0

    num_total = num_stmts + num_branches
    covered_total = covered_stmts + covered_branches
    combined_pct = round((covered_total / num_total * 100.0), 2) if num_total else 0.0

    return {
        "num_statements": num_stmts,
        "covered_statements": covered_stmts,
        "statement_pct": stmt_pct,
        "num_branches": num_branches,
        "covered_branches": covered_branches,
        "branch_pct": branch_pct,
        "num_total": num_total,
        "covered_total": covered_total,
        "combined_pct": combined_pct,
    }


def check_coverage_claims(
    cov_path: Path | None = None,
    doc_files: list[Path] | None = None,
    verification_path: Path | None = None,
) -> list[str]:
    violations = []
    if cov_path is None:
        cov_path = ROOT / "test-results" / "coverage.json"

    if not cov_path.exists():
        violations.append(
            f"Coverage report {cov_path} not found. Pytest coverage JSON must be generated before auditing claims."
        )
        return violations

    try:
        with open(cov_path, "r", encoding="utf-8") as f:
            cov_raw = json.load(f)
    except Exception as e:
        violations.append(f"Failed to parse coverage JSON at {cov_path}: {e}")
        return violations

    cov = parse_coverage_totals(cov_raw)
    stmt_pct = cov["statement_pct"]
    branch_pct = cov["branch_pct"]
    combined_pct = cov["combined_pct"]
    covered_stmts = cov["covered_statements"]
    num_stmts = cov["num_statements"]
    covered_branches = cov["covered_branches"]
    num_branches = cov["num_branches"]

    if doc_files is None:
        doc_files = list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))

    for file_path in doc_files:
        rel_path = file_path.relative_to(ROOT) if file_path.is_relative_to(ROOT) else file_path.name
        content = file_path.read_text(encoding="utf-8")

        for line_no, line in enumerate(content.splitlines(), start=1):
            lower_line = line.lower()
            # Skip lines defining threshold rules/criteria (e.g. >= 85% or minimum threshold)
            if any(k in lower_line for k in [">=", "<=", "threshold", "minimum threshold", "--cov-fail-under"]):
                continue

            # 1. Statement coverage % claims: e.g. "92.98% statement coverage" or "92.98% Stmt"
            for m in re.finditer(r"(\d+\.\d+)%\s*(?:statement|Stmt)", line, re.IGNORECASE):
                val = float(m.group(1))
                if abs(val - stmt_pct) > 0.01:
                    violations.append(
                        f"{rel_path}:{line_no} — Documented statement coverage claim '{val}%' does not match coverage.json metric '{stmt_pct}%' ({covered_stmts}/{num_stmts})"
                    )

            # 2. Branch coverage % claims: e.g. "81.85% unrounded branch coverage" or "81.85% Branch"
            for m in re.finditer(r"(\d+\.\d+)%\s*(?:unrounded\s+)?(?:branch|Branch)", line, re.IGNORECASE):
                val = float(m.group(1))
                if abs(val - branch_pct) > 0.01:
                    violations.append(
                        f"{rel_path}:{line_no} — Documented branch coverage claim '{val}%' does not match coverage.json metric '{branch_pct}%' ({covered_branches}/{num_branches})"
                    )

            # 3. Combined coverage % claims: e.g. "90.24% combined coverage"
            for m in re.finditer(r"(\d+\.\d+)%\s+combined\s+coverage", line, re.IGNORECASE):
                val = float(m.group(1))
                if abs(val - combined_pct) > 0.01:
                    violations.append(
                        f"{rel_path}:{line_no} — Documented combined coverage claim '{val}%' does not match coverage.json metric '{combined_pct}%' ({cov['covered_total']}/{cov['num_total']})"
                    )

            # 4. Covered statements fraction: e.g. "1,471/1,582 statements"
            for m in re.finditer(r"(\d[\d,]*)\s*/\s*(\d[\d,]*)\s+statements", line, re.IGNORECASE):
                c_val = int(m.group(1).replace(",", ""))
                t_val = int(m.group(2).replace(",", ""))
                if c_val != covered_stmts or t_val != num_stmts:
                    violations.append(
                        f"{rel_path}:{line_no} — Documented statement fraction '{c_val}/{t_val}' does not match coverage.json '{covered_stmts}/{num_stmts}'"
                    )

            # 5. Covered branches fraction: e.g. "424/518 branches"
            for m in re.finditer(r"(\d[\d,]*)\s*/\s*(\d[\d,]*)\s+branches", line, re.IGNORECASE):
                c_val = int(m.group(1).replace(",", ""))
                t_val = int(m.group(2).replace(",", ""))
                if c_val != covered_branches or t_val != num_branches:
                    violations.append(
                        f"{rel_path}:{line_no} — Documented branch fraction '{c_val}/{t_val}' does not match coverage.json '{covered_branches}/{num_branches}'"
                    )

    # Reconcile docs/verification-results.json
    if verification_path is None:
        verification_path = ROOT / "docs" / "verification-results.json"
    if verification_path.exists():
        try:
            with open(verification_path, "r", encoding="utf-8") as f:
                vr = json.load(f)
            vr_pytest = vr.get("gates", {}).get("pytest", {})
            vr_stmt = vr_pytest.get("statement_coverage_percent")
            vr_branch = vr_pytest.get("branch_coverage_percent")
            vr_comb = vr_pytest.get("coverage_percent")
            if vr_stmt is not None and abs(vr_stmt - stmt_pct) > 0.01:
                violations.append(
                    f"verification-results.json: statement_coverage_percent '{vr_stmt}' does not match coverage.json '{stmt_pct}'"
                )
            if vr_branch is not None and abs(vr_branch - branch_pct) > 0.01:
                violations.append(
                    f"verification-results.json: branch_coverage_percent '{vr_branch}' does not match coverage.json '{branch_pct}'"
                )
            if vr_comb is not None and abs(vr_comb - combined_pct) > 0.01:
                violations.append(
                    f"verification-results.json: coverage_percent '{vr_comb}' does not match coverage.json '{combined_pct}'"
                )
        except Exception as e:
            violations.append(f"Failed to check coverage in {verification_path}: {e}")

    return violations


def main() -> int:
    print("=" * 60)
    print("  EXCURSIONLENS DOCUMENTATION & CLAIMS AUDIT")
    print("=" * 60)

    claims_violations = check_markdown_claims()
    id_violations = check_authoritative_identifiers()
    cov_violations = check_coverage_claims()
    prov_violations = check_receipt_provenance()

    all_violations = claims_violations + id_violations + cov_violations + prov_violations

    if all_violations:
        print(f"❌ Claims audit failed with {len(all_violations)} violation(s):")
        for v in all_violations:
            print(f"   • {v}")
        return 1

    print("✅ Documentation & Claims Audit Passed! Zero overclaims, stale metrics, or invalid identifiers found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
