from unittest.mock import AsyncMock, Mock, patch

import pytest

from tasks_mcp.client import api_request


@pytest.mark.asyncio
async def test_client_get_success():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={"id": "1", "title": "Test"})
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await api_request("items", method="GET")
        assert result["id"] == "1"
        assert result["title"] == "Test"


@pytest.mark.asyncio
async def test_client_post_with_json():
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json = Mock(return_value={"id": "2", "title": "Created"})
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await api_request(
            "items", method="POST", json_data={"title": "Created", "type": "task"}
        )
        assert result["id"] == "2"
