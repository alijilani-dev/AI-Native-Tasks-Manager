from unittest.mock import patch

import pytest

from tasks_mcp.tools.modify import tasks_modify


@pytest.mark.asyncio
async def test_modify_title():
    mock_item = {"id": "1", "title": "Updated title", "status": "pending"}
    with patch("tasks_mcp.tools.modify.update", return_value=mock_item):
        result = await tasks_modify(user_id="default", item_id="1", title="Updated title")
        assert "Updated title" in result


@pytest.mark.asyncio
async def test_modify_returns_error_on_404():
    with patch("tasks_mcp.tools.modify.update", return_value=None):
        result = await tasks_modify(user_id="default", item_id="999", title="New")
        assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_modify_description():
    mock_item = {"id": "1", "title": "Task", "description": "New desc"}
    with patch("tasks_mcp.tools.modify.update", return_value=mock_item):
        result = await tasks_modify(user_id="default", item_id="1", description="New desc")
        assert "New desc" in result


@pytest.mark.asyncio
async def test_modify_priority():
    mock_item = {"id": "1", "title": "Task", "priority": 5}
    with patch("tasks_mcp.tools.modify.update", return_value=mock_item):
        result = await tasks_modify(user_id="default", item_id="1", priority=5)
        assert '"priority": 5' in result


@pytest.mark.asyncio
async def test_modify_due_date():
    mock_item = {"id": "1", "title": "Task", "due_date": "2026-07-01T12:00:00Z"}
    with patch("tasks_mcp.tools.modify.update", return_value=mock_item):
        result = await tasks_modify(user_id="default", item_id="1", due_date="2026-07-01T12:00:00Z")
        assert "2026-07-01" in result


@pytest.mark.asyncio
async def test_modify_location():
    mock_item = {"id": "1", "title": "Task", "location": "Office"}
    with patch("tasks_mcp.tools.modify.update", return_value=mock_item):
        result = await tasks_modify(user_id="default", item_id="1", location="Office")
        assert "Office" in result


@pytest.mark.asyncio
async def test_modify_participants():
    mock_item = {"id": "1", "title": "Meeting", "participants": ["alice", "bob"]}
    with patch("tasks_mcp.tools.modify.update", return_value=mock_item):
        result = await tasks_modify(user_id="default", item_id="1", participants=["alice", "bob"])
        assert "alice" in result
        assert "bob" in result


@pytest.mark.asyncio
async def test_modify_wrong_user():
    with patch("tasks_mcp.tools.modify.update", return_value=None):
        result = await tasks_modify(user_id="wrong", item_id="1", title="Hack")
        assert "not found" in result.lower()
