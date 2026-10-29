"""
scripts/provenance.py - Shared Evidence Authority & Execution Provenance Resolver

Determines whether execution is occurring in an authoritative CI environment (GitHub Actions)
with all required context fields, or as a local documentation snapshot.
"""

import os
from typing import Tuple


def get_execution_provenance() -> Tuple[str, str]:
    """
    Returns (evidence_authority, execution_context).

    In GitHub Actions with valid environment fields:
      evidence_authority: "AUTHORITATIVE_CI_ARTIFACT"
      execution_context: "https://github.com/<owner>/<repo>/actions/runs/<run_id>"

    In local execution:
      evidence_authority: "LOCAL_DOCUMENTATION_SNAPSHOT"
      execution_context: "LOCAL_DOCUMENTATION_SNAPSHOT"
    """
    github_actions = os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true"
    github_server = os.environ.get("GITHUB_SERVER_URL", "").strip().rstrip("/")
    github_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    github_run_id = os.environ.get("GITHUB_RUN_ID", "").strip()

    is_authoritative_ci = bool(
        github_actions and github_server and github_repo and github_run_id
    )

    if is_authoritative_ci:
        return (
            "AUTHORITATIVE_CI_ARTIFACT",
            f"{github_server}/{github_repo}/actions/runs/{github_run_id}",
        )

    return (
        "LOCAL_DOCUMENTATION_SNAPSHOT",
        "LOCAL_DOCUMENTATION_SNAPSHOT",
    )

