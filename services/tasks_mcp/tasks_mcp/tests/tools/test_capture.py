from unittest.mock import patch

import pytest

from tasks_mcp.tools.capture import tasks_capture


@pytest.mark.asyncio
async def test_capture_task():
    mock_item = {"id": "1", "title": "Buy milk", "type": "task", "user_id": "default", "status": "pending"}
    with patch("tasks_mcp.tools.capture.create", return_value=mock_item):
        result = await tasks_capture(title="Buy milk", type="task")
        assert '"id": "1"' in result
        assert "Buy milk" in result


@pytest.mark.asyncio
async def test_capture_appointment():
    mock_item = {
        "id": "2", "title": "Dentist", "type": "appointment",
        "start_time": "2026-05-10T14:00:00Z", "user_id": "default",
    }
    with patch("tasks_mcp.tools.capture.create", return_value=mock_item):
        result = await tasks_capture(title="Dentist", type="appointment", start_time="2026-05-10T14:00:00Z")
        assert "appointment" in result
        assert "2026-05-10T14:00:00Z" in result


@pytest.mark.asyncio
async def test_capture_default_user_id():
    mock_item = {"id": "3", "title": "Test", "type": "task", "user_id": "default"}
    with patch("tasks_mcp.tools.capture.create", return_value=mock_item):
        result = await tasks_capture(title="Test", type="task")
        assert '"user_id": "default"' in result


@pytest.mark.asyncio
async def test_capture_with_all_fields():
    mock_item = {
        "id": "4", "title": "Full item", "type": "task", "user_id": "alice",
        "description": "Details", "priority": 3,
        "due_date": "2026-06-01T12:00:00Z", "reminder_at": "2026-06-01T11:00:00Z",
        "location": "Home", "participants": ["bob"],
    }
    with patch("tasks_mcp.tools.capture.create", return_value=mock_item):
        result = await tasks_capture(
            title="Full item", type="task", user_id="alice",
            description="Details", priority=3,
            due_date="2026-06-01T12:00:00Z", reminder_at="2026-06-01T11:00:00Z",
            location="Home", participants=["bob"],
        )
        assert "alice" in result
        assert "Details" in result
        assert "Home" in result
        assert "bob" in result


@pytest.mark.asyncio
async def test_capture_idempotency():
    mock_item = {"id": "dup-id", "title": "Dup", "type": "task"}
    with patch("tasks_mcp.tools.capture.create", return_value=mock_item) as mock_create:
        result1 = await tasks_capture(title="Dup", type="task", idempotency_key="abc-123")
        result2 = await tasks_capture(title="Dup", type="task", idempotency_key="abc-123")
        assert "dup-id" in result1
        assert result1 == result2
        assert mock_create.call_count == 2
