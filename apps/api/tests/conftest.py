"""
apps/api/tests/conftest.py — Pytest Configuration for ExcursionLens API Tests

Ensures deterministic, platform-independent test execution and reproducible
coverage metrics matching authoritative Linux CI.
"""

import os

# Set a canonical fallback GITHUB_SHA if not already present in environment,
# ensuring _get_git_commit_sha() takes the canonical fast path across all platforms.
# Uses an explicitly synthetic 40-character test-only SHA (all zeros).
if not os.environ.get("GITHUB_SHA") and not os.environ.get("APP_COMMIT_SHA") and not os.environ.get("GIT_COMMIT"):
    os.environ["GITHUB_SHA"] = "0000000000000000000000000000000000000000"
