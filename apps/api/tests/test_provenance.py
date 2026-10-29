"""
apps/api/tests/test_provenance.py - Tests for Evidence Authority, Provenance & Exact SHA Enforcement

Validates:
1. get_execution_provenance correctly identifies authoritative CI vs local documentation snapshots.
2. Local and CI environments can never be confused.
3. Strict exact-SHA enforcement in evaluate_smoke_receipt without compatibility waivers.
"""

import os
from unittest.mock import patch

import pytest
from scripts.provenance import get_execution_provenance
from scripts.verify import evaluate_smoke_receipt


def test_provenance_local_execution_when_env_clean():
    clean_env = {
        k: v for k, v in os.environ.items()
        if not k.startswith("GITHUB_")
    }
    with patch.dict(os.environ, clean_env, clear=True):
        authority, context = get_execution_provenance()
        assert authority == "LOCAL_DOCUMENTATION_SNAPSHOT"
        assert context == "LOCAL_DOCUMENTATION_SNAPSHOT"


def test_provenance_authoritative_ci_execution():
    ci_env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "abhijeetnardele24-hash/excursionlens",
        "GITHUB_RUN_ID": "987654321",
    }
    with patch.dict(os.environ, ci_env, clear=True):
        authority, context = get_execution_provenance()
        assert authority == "AUTHORITATIVE_CI_ARTIFACT"
        assert context == "https://github.com/abhijeetnardele24-hash/excursionlens/actions/runs/987654321"


@pytest.mark.parametrize(
    "missing_var",
    ["GITHUB_ACTIONS", "GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"],
)
def test_provenance_cannot_confuse_incomplete_ci_with_authoritative(missing_var: str):
    full_env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "abhijeetnardele24-hash/excursionlens",
        "GITHUB_RUN_ID": "987654321",
    }
    full_env.pop(missing_var)
    with patch.dict(os.environ, full_env, clear=True):
        authority, context = get_execution_provenance()
        assert authority == "LOCAL_DOCUMENTATION_SNAPSHOT"
        assert context == "LOCAL_DOCUMENTATION_SNAPSHOT"


def test_exact_sha_enforcement_blocks_mismatches_and_waivers():
    head_sha = "abc0000000000000000000000000000000000001"
    stale_sha = "abc0000000000000000000000000000000000000"

    # 1. Matching SHA accepts status
    smoke_ok = {"status": "LIVE_VERIFIED", "commit_sha": head_sha}
    status, reason = evaluate_smoke_receipt(smoke_ok, head_sha)
    assert status == "LIVE_VERIFIED"
    assert reason is None

    # 2. Mismatched SHA (even parent commit / previous run) is blocked with STALE_EVIDENCE
    smoke_stale = {"status": "LIVE_VERIFIED", "commit_sha": stale_sha}
    status, reason = evaluate_smoke_receipt(smoke_stale, head_sha)
    assert status == "BLOCKED/STALE_EVIDENCE"
    assert reason == "STALE_EVIDENCE"

    # 3. Missing receipt SHA fails closed
    smoke_no_sha = {"status": "LIVE_VERIFIED"}
    status, reason = evaluate_smoke_receipt(smoke_no_sha, head_sha)
    assert status == "BLOCKED/STALE_EVIDENCE"
    assert reason == "STALE_EVIDENCE"

