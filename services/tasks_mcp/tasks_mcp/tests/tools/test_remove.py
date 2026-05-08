from unittest.mock import patch

import pytest

from tasks_mcp.tools.remove import tasks_remove


@pytest.mark.asyncio
async def test_remove_success():
    with patch("tasks_mcp.tools.remove.delete", return_value=True):
        result = await tasks_remove(user_id="default", item_id="1")
        assert "deleted" in result.lower()


@pytest.mark.asyncio
async def test_remove_404():
    with patch("tasks_mcp.tools.remove.delete", return_value=False):
        result = await tasks_remove(user_id="default", item_id="999")
        assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_remove_accepts_idempotency_key():
    with patch("tasks_mcp.tools.remove.delete", return_value=True):
        result = await tasks_remove(user_id="default", item_id="1", idempotency_key="key-1")
        assert "deleted" in result.lower()
