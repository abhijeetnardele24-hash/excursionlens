"""
apps/api/tests/conftest.py — Pytest Configuration for ExcursionLens API Tests

Ensures deterministic, platform-independent test execution and reproducible
coverage metrics matching authoritative Linux CI.
"""

import os

# Set a canonical fallback GITHUB_SHA if not already present in environment,
# ensuring _get_git_commit_sha() takes the canonical fast path across all platforms.
if not os.environ.get("GITHUB_SHA") and not os.environ.get("APP_COMMIT_SHA") and not os.environ.get("GIT_COMMIT"):
    os.environ["GITHUB_SHA"] = "1837e00facd0f4d27906255472d9be2a339885b4"
