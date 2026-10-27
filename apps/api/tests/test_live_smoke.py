"""
apps/api/tests/test_live_smoke.py — Mocked Regression Tests for Fail-Closed Live Smoke Verifier
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import httpx

ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.live_smoke import verify_nebius, verify_tavily  # noqa: E402


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
