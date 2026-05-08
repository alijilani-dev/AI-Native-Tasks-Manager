import pytest

# Import server first so all tools and health endpoint register on mcp
import tasks_mcp.server  # noqa: F401
from tasks_mcp.mcp_instance import mcp


def test_server_name():
    assert mcp.name == "tasks_mcp"


def test_server_has_health_tool():
    tools = mcp._tool_manager.list_tools()
    names = [t.name for t in tools]
    assert "health" in names


def test_tools_registered():
    tools = mcp._tool_manager.list_tools()
    names = [t.name for t in tools]
    expected = {"health", "tasks_capture", "tasks_review", "tasks_modify", "tasks_resolve", "tasks_remove"}
    assert expected.issubset(set(names)), f"Missing tools: {expected - set(names)}"


@pytest.mark.asyncio
async def test_health_returns_ok():
    result = await mcp.call_tool("health", {})
    text = result[0][0].text
    assert '"status": "ok"' in text
