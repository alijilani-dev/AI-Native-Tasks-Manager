import json
from unittest.mock import patch

import pytest

from tasks_mcp.tools.review import tasks_review


def _mock_data(items, total=None, offset=0):
    return {"items": items, "total": total or len(items), "offset": offset}


@pytest.mark.asyncio
async def test_review_returns_items():
    mock_data = _mock_data([{"id": "1", "title": "Buy milk", "status": "pending"}], total=1)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data):
        result = await tasks_review(user_id="default")
        assert "Buy milk" in result


@pytest.mark.asyncio
async def test_review_empty():
    mock_data = _mock_data([], total=0)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data):
        result = await tasks_review(user_id="default", response_format="markdown")
        assert "0 items" in result


@pytest.mark.asyncio
async def test_review_pagination_defaults():
    mock_data = _mock_data([{"id": str(i)} for i in range(20)], total=50)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data):
        result = await tasks_review(user_id="default")
        parsed = json.loads(result)
        assert parsed["offset"] == 0
        assert parsed["count"] == 20


@pytest.mark.asyncio
async def test_review_filters_status():
    mock_data = _mock_data([{"id": "1", "title": "Done", "status": "completed"}], total=1)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data) as mk:
        await tasks_review(user_id="default", status="completed")
        assert mk.call_args[1].get("status") == "completed"


@pytest.mark.asyncio
async def test_review_filters_type():
    mock_data = _mock_data([{"id": "1", "title": "Event", "type": "appointment"}], total=1)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data) as mk:
        await tasks_review(user_id="default", type="appointment")
        assert mk.call_args[1].get("item_type") == "appointment"


@pytest.mark.asyncio
async def test_review_filters_search_text():
    mock_data = _mock_data([{"id": "1", "title": "Buy milk", "status": "pending"}], total=1)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data) as mk:
        await tasks_review(user_id="default", search_text="milk")
        assert mk.call_args[1].get("search_text") == "milk"


@pytest.mark.asyncio
async def test_review_filters_date_range():
    mock_data = _mock_data([], total=0)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data) as mk:
        await tasks_review(user_id="default", date_from="2026-01-01", date_to="2026-12-31")
        assert mk.call_args[1].get("date_from") == "2026-01-01"
        assert mk.call_args[1].get("date_to") == "2026-12-31"


@pytest.mark.asyncio
async def test_review_filters_overdue():
    mock_data = _mock_data([{"id": "1", "title": "Overdue", "status": "pending"}], total=1)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data) as mk:
        await tasks_review(user_id="default", is_overdue=True)
        assert mk.call_args[1].get("is_overdue") is True


@pytest.mark.asyncio
async def test_review_filters_priority():
    mock_data = _mock_data([{"id": "1", "title": "Important", "priority": 1}], total=1)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data) as mk:
        await tasks_review(user_id="default", priority=1)
        assert mk.call_args[1].get("priority") == 1


@pytest.mark.asyncio
async def test_review_markdown_format():
    items = [{"id": "1", "title": "Task A", "status": "pending"}]
    mock_data = _mock_data(items, total=1)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data):
        result = await tasks_review(user_id="default", response_format="markdown")
        assert result.startswith("#")


@pytest.mark.asyncio
async def test_review_clamps_limit():
    mock_data = _mock_data([], total=0)
    with patch("tasks_mcp.tools.review.list_items", return_value=mock_data) as mk:
        await tasks_review(user_id="default", limit=999)
        assert mk.call_args[1].get("limit") == 100
