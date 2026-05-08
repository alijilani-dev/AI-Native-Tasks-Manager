from unittest.mock import patch

import pytest

from tasks_mcp.tools.resolve import tasks_resolve


@pytest.mark.asyncio
async def test_resolve_completed():
    mock_item = {"id": "1", "title": "Report", "status": "completed"}
    with patch("tasks_mcp.tools.resolve.resolve", return_value=mock_item):
        result = await tasks_resolve(user_id="default", item_id="1", status="completed")
        assert "completed" in result


@pytest.mark.asyncio
async def test_resolve_cancelled():
    mock_item = {"id": "1", "title": "Event", "status": "cancelled"}
    with patch("tasks_mcp.tools.resolve.resolve", return_value=mock_item):
        result = await tasks_resolve(user_id="default", item_id="1", status="cancelled")
        assert "cancelled" in result


@pytest.mark.asyncio
async def test_resolve_with_note():
    mock_item = {"id": "1", "title": "Task", "status": "completed", "resolution_note": "Done well"}
    with patch("tasks_mcp.tools.resolve.resolve", return_value=mock_item):
        result = await tasks_resolve(user_id="default", item_id="1", status="completed", note="Done well")
        assert "Done well" in result


@pytest.mark.asyncio
async def test_resolve_skipped():
    mock_item = {"id": "1", "title": "Gym", "status": "skipped"}
    with patch("tasks_mcp.tools.resolve.resolve", return_value=mock_item):
        result = await tasks_resolve(user_id="default", item_id="1", status="skipped")
        assert "skipped" in result


@pytest.mark.asyncio
async def test_resolve_404():
    with patch("tasks_mcp.tools.resolve.resolve", return_value=None):
        result = await tasks_resolve(user_id="default", item_id="999", status="completed")
        assert "not found" in result.lower()
