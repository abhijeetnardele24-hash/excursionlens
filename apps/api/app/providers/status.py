"""
apps/api/app/providers/status.py — Runtime Provider & Application Status Evaluator
"""

from typing import Literal

ProviderStatus = Literal[
    "NOT_CONFIGURED",
    "CONFIGURED_PENDING_VERIFICATION",
    "LIVE_VERIFIED",
    "PARTIAL_FAILURE",
    "DEMO_FIXTURE",
    "DEMO_FIXTURE_FALLBACK",
]


def is_valid_credential(key: str | None) -> bool:
    if not key:
        return False
    k = key.strip()
    if not k:
        return False
    lower = k.lower()
    if lower.startswith("your_") or lower.startswith("placeholder") or lower == "none" or lower == "<none>":
        return False
    return True


def evaluate_runtime_status(
    nebius_key: str | None,
    tavily_key: str | None,
    app_mode: str = "live",
    verified_live_run: bool = False,
    failed_live_attempt: bool = False,
) -> tuple[ProviderStatus, str, bool]:
    """
    Evaluates provider status, provider mode, and live execution verification.

    Returns:
        (provider_status, provider_mode, live_execution_verified)

    Rules:
    - Never returns LIVE_VERIFIED unless verified_live_run is True.
    - If app_mode is explicitly 'fixture', returns DEMO_FIXTURE.
    - If neither key is configured, returns NOT_CONFIGURED with DEMO_FIXTURE mode.
    - If only one key is configured, returns PARTIAL_FAILURE with DEMO_FIXTURE_FALLBACK mode.
    - If both keys configured but unverified, returns CONFIGURED_PENDING_VERIFICATION with DEMO_FIXTURE mode.
    - If live execution attempted and failed, returns DEMO_FIXTURE_FALLBACK.
    - If verified_live_run is True and both keys configured, returns LIVE_VERIFIED with LIVE_TOKEN_FACTORY mode.
    """
    if app_mode.lower() == "fixture":
        return "DEMO_FIXTURE", "DEMO_FIXTURE", False

    has_nebius = is_valid_credential(nebius_key)
    has_tavily = is_valid_credential(tavily_key)

    if not has_nebius and not has_tavily:
        return "NOT_CONFIGURED", "DEMO_FIXTURE", False

    if (has_nebius and not has_tavily) or (has_tavily and not has_nebius):
        return "PARTIAL_FAILURE", "DEMO_FIXTURE_FALLBACK", False

    # Both keys are configured
    if verified_live_run:
        return "LIVE_VERIFIED", "LIVE_TOKEN_FACTORY", True

    if failed_live_attempt:
        return "DEMO_FIXTURE_FALLBACK", "DEMO_FIXTURE_FALLBACK", False

    return "CONFIGURED_PENDING_VERIFICATION", "DEMO_FIXTURE", False
