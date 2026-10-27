"""
apps/api/tests/test_nebius_catalog.py — Contract tests for Nebius Model Discovery
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from apps.api.app.providers.nebius import NebiusTokenFactoryProvider


def test_discover_models_missing_key():
    provider = NebiusTokenFactoryProvider(api_key="")
    res = provider.discover_models()
    assert res["status"] == "NOT_CONFIGURED"
    assert res["error_category"] == "MISSING_KEY"
    assert res["selected_deep_model"] is None


def test_discover_models_failed_http_500():
    provider = NebiusTokenFactoryProvider(api_key="valid-dummy-key-for-testing")
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with MagicMock(spec=httpx.Client) as mock_client:
        mock_client.get.return_value = mock_resp
        # Patch httpx.Client in discover_models
        from unittest.mock import patch
        with patch("apps.api.app.providers.nebius.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value = mock_client
            res = provider.discover_models()

    assert res["status"] == "FAILED"
    assert res["error_category"] == "HTTP_500"
    assert res["selected_deep_model"] is None


def test_discover_models_empty_catalog():
    provider = NebiusTokenFactoryProvider(api_key="valid-dummy-key-for-testing")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": []}

    from unittest.mock import patch
    with patch("apps.api.app.providers.nebius.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
        res = provider.discover_models()

    assert res["status"] == "FAILED"
    assert res["error_category"] == "NO_NVIDIA_MODELS"
    assert res["selected_deep_model"] is None


def test_discover_models_non_nvidia_catalog():
    provider = NebiusTokenFactoryProvider(api_key="valid-dummy-key-for-testing")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "meta-llama/Llama-3-8b-chat-hf"},
            {"id": "mistralai/Mistral-7B-Instruct-v0.2"}
        ]
    }

    from unittest.mock import patch
    with patch("apps.api.app.providers.nebius.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
        res = provider.discover_models()

    # Must never return LIVE_SUCCESS with 0 NVIDIA models
    assert res["status"] == "FAILED"
    assert res["error_category"] == "NO_NVIDIA_MODELS"
    assert res["selected_deep_model"] is None


def test_discover_models_valid_nvidia_catalog():
    provider = NebiusTokenFactoryProvider(
        api_key="valid-dummy-key-for-testing",
        deep_model_id="nvidia/llama-3.1-nemotron-70b-instruct"
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"id": "nvidia/nemotron-mini-4b-instruct"},
            {"id": "nvidia/llama-3.1-nemotron-70b-instruct"}
        ]
    }

    from unittest.mock import patch
    with patch("apps.api.app.providers.nebius.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
        res = provider.discover_models()

    assert res["status"] == "LIVE_SUCCESS"
    assert res["selected_deep_model"] == "nvidia/llama-3.1-nemotron-70b-instruct"
    assert res["selected_fast_model"] == "nvidia/nemotron-mini-4b-instruct"
    assert len(res["nvidia_models"]) == 2


@pytest.mark.asyncio
async def test_discover_models_async_valid():
    provider = NebiusTokenFactoryProvider(
        api_key="valid-dummy-key-for-testing",
        deep_model_id="nvidia/llama-3.1-nemotron-70b-instruct"
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"id": "nvidia/llama-3.1-nemotron-70b-instruct"}]
    }
    mock_client.get.return_value = mock_resp

    res = await provider.discover_models_async(client=mock_client)
    assert res["status"] == "LIVE_SUCCESS"
    assert res["selected_deep_model"] == "nvidia/llama-3.1-nemotron-70b-instruct"
