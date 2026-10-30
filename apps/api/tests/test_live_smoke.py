"""
apps/api/tests/test_live_smoke.py — Mocked Regression Tests for Fail-Closed Live Smoke Verifier
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.live_smoke import is_valid_live_smoke_url, verify_nebius, verify_tavily  # noqa: E402
from scripts.verify import evaluate_smoke_receipt  # noqa: E402


def test_tavily_missing_key():
    receipt, failures = verify_tavily("")
    assert receipt["status"] == "MISSING_KEY"
    assert "TAVILY_API_KEY is not configured" in failures[0]


def test_tavily_empty_results_http_200():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": []}

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    receipt, failures = verify_tavily("mock_key_tvly_valid_length_here", client=mock_client)
    assert receipt["status"] == "NO_VALID_RESULTS"
    assert "0 usable results" in failures[0]


def test_tavily_disallowed_domain_and_non_https():
    # Result 1: Non-HTTPS (http://cdc.gov)
    # Result 2: Disallowed domain (https://untrusted-blog.com)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"url": "http://cdc.gov/storage", "content": "Good domain but insecure HTTP"},
            {"url": "https://untrusted-blog.com/storage", "content": "HTTPS but untrusted domain"},
        ]
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    receipt, failures = verify_tavily("mock_key_tvly_valid_length_here", client=mock_client)
    assert receipt["status"] == "NO_VALID_RESULTS"
    assert receipt["results_count"] == 0


def test_tavily_valid_allowlisted_https():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "url": "https://www.cdc.gov/vaccines/storage.html",
                "content": "CDC temperature excursion response guidance",
                "title": "CDC Storage"
            }
        ]
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    receipt, failures = verify_tavily("mock_key_tvly_valid_length_here", client=mock_client)
    assert receipt["status"] == "LIVE_SUCCESS"
    assert receipt["results_count"] == 1
    assert "www.cdc.gov" in receipt["source_domains"]
    assert len(receipt["source_digests"]) == 1
    assert len(failures) == 0


def test_nebius_missing_key():
    receipt, failures = verify_nebius("", "https://api.tokenfactory.nebius.com/v1/", "nvidia/nemotron")
    assert receipt["status"] == "MISSING_KEY"
    assert "NEBIUS_TOKEN_FACTORY_KEY is not configured" in failures[0]


def test_nebius_empty_catalog():
    cat_resp = MagicMock()
    cat_resp.status_code = 200
    cat_resp.json.return_value = {"data": []}

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = cat_resp

    receipt, failures = verify_nebius("neb-test-key-long-enough-1234", "https://api.tokenfactory.nebius.com/v1/", "nvidia/nemotron", client=mock_client)
    assert receipt["status"] == "EMPTY_CATALOG"
    assert "empty 'data' array" in failures[0]


def test_nebius_catalog_no_nvidia_models():
    cat_resp = MagicMock()
    cat_resp.status_code = 200
    cat_resp.json.return_value = {"data": [{"id": "meta/llama-3-8b-instruct"}, {"id": "mistral/mistral-7b"}]}

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = cat_resp

    receipt, failures = verify_nebius("neb-test-key-long-enough-1234", "https://api.tokenfactory.nebius.com/v1/", "nvidia/nemotron", client=mock_client)
    assert receipt["status"] == "NO_NVIDIA_MODELS"
    assert "0 NVIDIA or Nemotron models" in failures[0]


def test_nebius_empty_choices_http_200():
    cat_resp = MagicMock()
    cat_resp.status_code = 200
    cat_resp.json.return_value = {"data": [{"id": "nvidia/llama-3.1-nemotron-70b-instruct"}]}

    chat_resp = MagicMock()
    chat_resp.status_code = 200
    chat_resp.json.return_value = {"choices": [], "usage": {}}

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = cat_resp
    mock_client.post.return_value = chat_resp

    receipt, failures = verify_nebius("neb-test-key-long-enough-1234", "https://api.tokenfactory.nebius.com/v1/", "nvidia/llama-3.1-nemotron-70b-instruct", client=mock_client)
    assert receipt["status"] == "EMPTY_CHOICES"
    assert "empty choices" in failures[0]


def test_nebius_malformed_json_content():
    cat_resp = MagicMock()
    cat_resp.status_code = 200
    cat_resp.json.return_value = {"data": [{"id": "nvidia/llama-3.1-nemotron-70b-instruct"}]}

    chat_resp = MagicMock()
    chat_resp.status_code = 200
    chat_resp.json.return_value = {
        "choices": [{"message": {"content": "This is raw text, not JSON."}}],
        "usage": {"total_tokens": 50}
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = cat_resp
    mock_client.post.return_value = chat_resp

    receipt, failures = verify_nebius("neb-test-key-long-enough-1234", "https://api.tokenfactory.nebius.com/v1/", "nvidia/llama-3.1-nemotron-70b-instruct", client=mock_client)
    assert receipt["status"] == "MALFORMED_JSON"
    assert receipt["structured_output_valid"] is False


def test_nebius_missing_required_fields_json():
    cat_resp = MagicMock()
    cat_resp.status_code = 200
    cat_resp.json.return_value = {"data": [{"id": "nvidia/llama-3.1-nemotron-70b-instruct"}]}

    chat_resp = MagicMock()
    chat_resp.status_code = 200
    # Missing 'hypotheses' and 'recommended_posture'
    chat_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps({"incident_summary": "Summary here"})}}],
        "usage": {"total_tokens": 80}
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = cat_resp
    mock_client.post.return_value = chat_resp

    receipt, failures = verify_nebius("neb-test-key-long-enough-1234", "https://api.tokenfactory.nebius.com/v1/", "nvidia/llama-3.1-nemotron-70b-instruct", client=mock_client)
    assert receipt["status"] == "MISSING_FIELD_HYPOTHESES"
    assert receipt["structured_output_valid"] is False


def test_nebius_valid_structured_output():
    cat_resp = MagicMock()
    cat_resp.status_code = 200
    cat_resp.json.return_value = {"data": [{"id": "nvidia/llama-3.1-nemotron-70b-instruct"}]}

    valid_payload = {
        "incident_summary": "Incident occurred due to door opening.",
        "hypotheses": ["Hypothesis 1: Cold air loss"],
        "recommended_posture": "QUARANTINE_PENDING_QUALIFIED_REVIEW"
    }

    chat_resp = MagicMock()
    chat_resp.status_code = 200
    chat_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(valid_payload)}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = cat_resp
    mock_client.post.return_value = chat_resp

    receipt, failures = verify_nebius("neb-test-key-long-enough-1234", "https://api.tokenfactory.nebius.com/v1/", "nvidia/llama-3.1-nemotron-70b-instruct", client=mock_client)
    assert receipt["status"] == "LIVE_SUCCESS"
    assert receipt["structured_output_valid"] is True
    assert receipt["selected_catalog_model"] == "nvidia/llama-3.1-nemotron-70b-instruct"
    assert receipt["response_digest"] is not None
    assert len(failures) == 0


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.cdc.gov/path", True),
        ("https://cdc.gov:443/path", True),
        ("https://cdc.gov:443@evil.example/path", False),
        ("https://cdc.gov.evil.example/path", False),
        ("https://evilcdc.gov/path", False),
        ("https://cdc.gov:invalid_port/path", False),
        ("http://www.cdc.gov/path", False),
        ("", False),
    ],
)
def test_live_smoke_url_validation_security(url: str, expected: bool):
    assert is_valid_live_smoke_url(url) is expected


def test_tavily_rejects_lookalikes_and_userinfo_tricks():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"url": "https://cdc.gov:443@evil.example/path", "content": "Phishing attack spoofing domain in userinfo"},
            {"url": "https://cdc.gov.evil.example/path", "content": "Lookalike subdomain attack"},
            {"url": "https://evilcdc.gov/path", "content": "Suffix lookalike attack"},
            {"url": "https://www.cdc.gov/path", "content": "Legitimate CDC guidance"},
        ]
    }
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    receipt, failures = verify_tavily("mock_key_tvly_valid_length_here", client=mock_client)
    assert receipt["status"] == "LIVE_SUCCESS"
    assert receipt["results_count"] == 1
    assert receipt["source_domains"] == ["www.cdc.gov"]
    assert len(failures) == 0


def test_parent_commit_live_receipt_cannot_verify_head():
    head_sha = "6f4fe62514053f059969582a4a6d2036a0e57ccb"
    parent_sha = "4e6164c111bd89ee3590400614e212d545ba8f85"

    parent_receipt = {
        "status": "LIVE_VERIFIED",
        "commit_sha": parent_sha,
        "timestamp": "2026-10-29T06:00:00Z",
    }

    status, reason = evaluate_smoke_receipt(parent_receipt, current_head=head_sha)
    assert status == "BLOCKED/STALE_EVIDENCE"
    assert reason == "STALE_EVIDENCE"


def test_exact_commit_live_receipt_verifies_head():
    head_sha = "6f4fe62514053f059969582a4a6d2036a0e57ccb"

    matching_receipt = {
        "status": "LIVE_VERIFIED",
        "commit_sha": head_sha,
        "timestamp": "2026-10-29T06:00:00Z",
    }

    status, reason = evaluate_smoke_receipt(matching_receipt, current_head=head_sha)
    assert status == "LIVE_VERIFIED"
    assert reason is None


def test_nebius_only_success_without_tavily(monkeypatch):
    from scripts.live_smoke import run_live_smoke

    # Mock settings and env with Nebius key but empty Tavily key
    monkeypatch.setattr("scripts.live_smoke.settings.nebius_key", "neb-live-test-valid-key-123456")
    monkeypatch.setattr("scripts.live_smoke.settings.tavily_key", "")
    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_KEY", "neb-live-test-valid-key-123456")
    monkeypatch.setenv("TAVILY_API_KEY", "")

    # Mock verify_nebius to return success
    def mock_verify_nebius(key, base_url, deep_model, client=None):
        return {
            "tested_model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "selected_catalog_model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "status": "LIVE_SUCCESS",
            "latency_ms": 350,
            "prompt_tokens": 120,
            "completion_tokens": 80,
            "total_tokens": 200,
            "response_digest": "abcdef123456",
            "structured_output_valid": True,
            "key_present": True,
            "key_preview": "neb-...3456",
        }, []

    monkeypatch.setattr("scripts.live_smoke.verify_nebius", mock_verify_nebius)

    rc = run_live_smoke()
    assert rc == 0

    receipt_file = ROOT / "docs" / "live-smoke-receipt.json"
    with open(receipt_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "LIVE_TOKEN_FACTORY"
    assert data["nebius_smoke"]["status"] == "LIVE_SUCCESS"
    assert data["tavily_smoke"]["status"] == "OMITTED"
    assert data["provider_mode"] == "LIVE"


def test_missing_key_fail_closed_behavior(monkeypatch):
    from scripts.live_smoke import run_live_smoke

    monkeypatch.setattr("scripts.live_smoke.settings.nebius_key", "")
    monkeypatch.setattr("scripts.live_smoke.settings.tavily_key", "")
    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")

    rc = run_live_smoke()
    assert rc == 1

    receipt_file = ROOT / "docs" / "live-smoke-receipt.json"
    with open(receipt_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "BLOCKED"
    assert data["nebius_smoke"]["status"] == "MISSING_KEY"
    assert data["nebius_smoke"]["tested_model"] is None
    assert data["nebius_smoke"]["total_tokens"] is None
    assert data["provider_mode"] == "DEMO_FIXTURE"
    assert "evaluated_source_sha" in data
    assert "receipt_commit_sha" in data


