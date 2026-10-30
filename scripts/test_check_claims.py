"""
scripts/test_check_claims.py — Regression Test Suite for Automated Claims & Coverage Validator

Validates that:
1. Valid project documentation passes the claims and coverage audits with 0 violations.
2. Mismatched statement percentages in markdown fail the audit.
3. Mismatched branch percentages in markdown fail the audit.
4. Mismatched combined percentages in markdown fail the audit.
5. Mismatched covered statement or branch counts fail the audit.
6. Mismatched verification-results.json metrics fail the audit.
7. Prohibited stale patterns (93.43%, 82.43%, 90.71%, 1,478, 427/518) fail the audit.
8. Missing coverage files fail the audit safely.
9. Contradictory deployment endpoint commit fails provenance audit.
10. Blocked smoke receipt claiming served models fails provenance audit.
11. Malformed evaluated_source_sha fails provenance audit.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_claims import (  # noqa: E402
    check_authoritative_identifiers,
    check_coverage_claims,
    check_markdown_claims,
    check_receipt_provenance,
)


def create_mock_coverage_json(tmp_dir: Path, covered_stmts=1471, num_stmts=1582, covered_branches=424, num_branches=518) -> Path:
    cov_path = tmp_dir / "coverage.json"
    data = {
        "totals": {
            "covered_lines": covered_stmts,
            "num_statements": num_stmts,
            "covered_branches": covered_branches,
            "num_branches": num_branches,
        }
    }
    with open(cov_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return cov_path


def test_real_repo_claims_and_coverage():
    """Verify that actual repo files pass all claims and dynamic coverage validation."""
    m_violations = check_markdown_claims()
    assert len(m_violations) == 0, f"Unexpected markdown claims violations: {m_violations}"

    id_violations = check_authoritative_identifiers()
    assert len(id_violations) == 0, f"Unexpected identifier violations: {id_violations}"

    cov_violations = check_coverage_claims()
    assert len(cov_violations) == 0, f"Unexpected coverage claims violations: {cov_violations}"

    prov_violations = check_receipt_provenance()
    assert len(prov_violations) == 0, f"Unexpected provenance claims violations: {prov_violations}"


def test_mismatched_statement_coverage_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        cov_path = create_mock_coverage_json(tmp_dir)

        bad_md = tmp_dir / "BAD.md"
        bad_md.write_text("We achieved 99.90% statement coverage across our tests.", encoding="utf-8")

        violations = check_coverage_claims(cov_path=cov_path, doc_files=[bad_md])
        assert any("Documented statement coverage claim '99.9%' does not match" in v for v in violations), (
            f"Expected statement mismatch violation, got: {violations}"
        )


def test_mismatched_branch_coverage_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        cov_path = create_mock_coverage_json(tmp_dir)

        bad_md = tmp_dir / "BAD.md"
        bad_md.write_text("Verified with 75.00% unrounded branch coverage in CI.", encoding="utf-8")

        violations = check_coverage_claims(cov_path=cov_path, doc_files=[bad_md])
        assert any("Documented branch coverage claim '75.0%' does not match" in v for v in violations), (
            f"Expected branch mismatch violation, got: {violations}"
        )


def test_mismatched_combined_coverage_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        cov_path = create_mock_coverage_json(tmp_dir)

        bad_md = tmp_dir / "BAD.md"
        bad_md.write_text("Reporting 95.00% combined coverage under pytest.", encoding="utf-8")

        violations = check_coverage_claims(cov_path=cov_path, doc_files=[bad_md])
        assert any("Documented combined coverage claim '95.0%' does not match" in v for v in violations), (
            f"Expected combined coverage mismatch violation, got: {violations}"
        )


def test_mismatched_statement_count_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        cov_path = create_mock_coverage_json(tmp_dir, covered_stmts=1471, num_stmts=1582)

        bad_md = tmp_dir / "BAD.md"
        bad_md.write_text("Measured 1,478/1,582 statements in test run.", encoding="utf-8")

        violations = check_coverage_claims(cov_path=cov_path, doc_files=[bad_md])
        assert any("Documented statement fraction '1478/1582' does not match" in v for v in violations), (
            f"Expected statement count mismatch violation, got: {violations}"
        )


def test_mismatched_branch_count_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        cov_path = create_mock_coverage_json(tmp_dir, covered_branches=424, num_branches=518)

        bad_md = tmp_dir / "BAD.md"
        bad_md.write_text("Measured 427/518 branches in test run.", encoding="utf-8")

        violations = check_coverage_claims(cov_path=cov_path, doc_files=[bad_md])
        assert any("Documented branch fraction '427/518' does not match" in v for v in violations), (
            f"Expected branch count mismatch violation, got: {violations}"
        )


def test_mismatched_verification_results_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        cov_path = create_mock_coverage_json(tmp_dir, covered_stmts=1471, num_stmts=1582)

        empty_md = tmp_dir / "DOC.md"
        empty_md.write_text("Clean docs without inline metrics.", encoding="utf-8")

        vr_path = tmp_dir / "verification-results.json"
        vr_data = {
            "gates": {
                "pytest": {
                    "statement_coverage_percent": 93.43,
                    "branch_coverage_percent": 81.85,
                    "coverage_percent": 90.24,
                }
            }
        }
        with open(vr_path, "w", encoding="utf-8") as f:
            json.dump(vr_data, f, indent=2)

        violations = check_coverage_claims(cov_path=cov_path, doc_files=[empty_md], verification_path=vr_path)
        assert any("verification-results.json: statement_coverage_percent '93.43' does not match" in v for v in violations), (
            f"Expected verification-results statement mismatch violation, got: {violations}"
        )


def test_prohibited_stale_patterns_fail():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        stale_metrics = ["93.43%", "82.43%", "90.71%", "1,478 statements", "427/518 branches"]
        for metric in stale_metrics:
            md_path = tmp_dir / f"test_{abs(hash(metric))}.md"
            md_path.write_text(f"Notice: contains stale metric {metric} from previous run.\n", encoding="utf-8")
            violations = check_markdown_claims(doc_files=[md_path])
            assert len(violations) > 0, f"Expected prohibited pattern failure for '{metric}', got none."


def test_missing_coverage_file_fails():
    nonexistent = Path("/nonexistent/coverage.json")
    violations = check_coverage_claims(cov_path=nonexistent)
    assert any("not found" in v for v in violations), f"Expected missing file violation, got: {violations}"


def test_contradictory_endpoint_commit_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        receipt_path = tmp_dir / "deployment-receipt.json"
        data = {
            "evaluated_source_sha": "a" * 40,
            "receipt_commit_sha": "b" * 40,
            "evidence_authority": "LOCAL_DOCUMENTATION_SNAPSHOT",
            "execution_context": "LOCAL_DOCUMENTATION_SNAPSHOT",
            "status": "LIVE_DEPLOYED",
            "endpoint_commit": "c" * 40,  # Contradicts evaluated_source_sha
        }
        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        violations = check_receipt_provenance(docs_dir=tmp_dir)
        assert any("endpoint_commit" in v and "does not match" in v for v in violations)


def test_blocked_smoke_receipt_with_fake_model_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        receipt_path = tmp_dir / "live-smoke-receipt.json"
        data = {
            "evaluated_source_sha": "a" * 40,
            "receipt_commit_sha": "b" * 40,
            "evidence_authority": "LOCAL_DOCUMENTATION_SNAPSHOT",
            "execution_context": "LOCAL_DOCUMENTATION_SNAPSHOT",
            "status": "BLOCKED",
            "provider_mode": "DEMO_FIXTURE",
            "nebius_smoke": {
                "tested_model": "nvidia/llama-3.1-nemotron-70b-instruct",  # Prohibited when BLOCKED
                "total_tokens": None,
            },
        }
        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        violations = check_receipt_provenance(docs_dir=tmp_dir)
        assert any("status is BLOCKED but tested_model is" in v for v in violations)


def test_invalid_evaluated_source_sha_fails():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        receipt_path = tmp_dir / "deployment-receipt.json"
        data = {
            "evaluated_source_sha": "short-sha",
            "receipt_commit_sha": "b" * 40,
            "evidence_authority": "LOCAL_DOCUMENTATION_SNAPSHOT",
            "execution_context": "LOCAL_DOCUMENTATION_SNAPSHOT",
            "status": "BLOCKED",
        }
        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        violations = check_receipt_provenance(docs_dir=tmp_dir)
        assert any("must be 40-char SHA" in v for v in violations)


def main() -> int:
    print("Running check_claims regression tests...")
    tests = [
        test_real_repo_claims_and_coverage,
        test_mismatched_statement_coverage_fails,
        test_mismatched_branch_coverage_fails,
        test_mismatched_combined_coverage_fails,
        test_mismatched_statement_count_fails,
        test_mismatched_branch_count_fails,
        test_mismatched_verification_results_fails,
        test_prohibited_stale_patterns_fail,
        test_missing_coverage_file_fails,
        test_contradictory_endpoint_commit_fails,
        test_blocked_smoke_receipt_with_fake_model_fails,
        test_invalid_evaluated_source_sha_fails,
    ]

    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__} passed")
        except Exception as e:
            print(f"  ✗ {t.__name__} failed: {e}")
            return 1

    print(f"\n✅ All {len(tests)} regression tests passed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
