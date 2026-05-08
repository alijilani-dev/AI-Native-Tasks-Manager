import json

import pytest

from tasks_mcp.e2e.conftest import call_tool

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_capture_and_review(e2e_client, session_id):
    r = await call_tool(e2e_client, session_id, "tasks_capture", {
        "title": "Buy groceries", "type": "task", "priority": 3,
    })
    assert "result" in r
    data = json.loads(r["result"]["content"][0]["text"])
    assert data["title"] == "Buy groceries"
    task_id = data["id"]

    r = await call_tool(e2e_client, session_id, "tasks_capture", {
        "title": "Call dentist", "type": "appointment",
        "start_time": "2026-05-07T14:00:00Z", "end_time": "2026-05-07T15:00:00Z",
    })
    assert "result" in r

    r = await call_tool(e2e_client, session_id, "tasks_review", {"user_id": "default"})
    content = json.loads(r["result"]["content"][0]["text"])
    assert content["total"] >= 2
    ids = [item["id"] for item in content["items"]]
    assert task_id in ids


@pytest.mark.asyncio
async def test_modify(e2e_client, session_id):
    r = await call_tool(e2e_client, session_id, "tasks_capture", {
        "title": "Write report", "type": "task",
    })
    data = json.loads(r["result"]["content"][0]["text"])
    task_id = data["id"]

    r = await call_tool(e2e_client, session_id, "tasks_modify", {
        "user_id": "default", "item_id": task_id, "title": "Write final report",
    })
    content = r["result"]["content"][0]["text"]
    assert "Write final report" in content


@pytest.mark.asyncio
async def test_resolve(e2e_client, session_id):
    r = await call_tool(e2e_client, session_id, "tasks_capture", {
        "title": "Complete project", "type": "task",
    })
    data = json.loads(r["result"]["content"][0]["text"])
    task_id = data["id"]

    r = await call_tool(e2e_client, session_id, "tasks_resolve", {
        "user_id": "default", "item_id": task_id, "status": "completed",
    })
    content = r["result"]["content"][0]["text"]
    assert "completed" in content


@pytest.mark.asyncio
async def test_remove(e2e_client, session_id):
    r = await call_tool(e2e_client, session_id, "tasks_capture", {
        "title": "Temp", "type": "task",
    })
    data = json.loads(r["result"]["content"][0]["text"])
    task_id = data["id"]

    r = await call_tool(e2e_client, session_id, "tasks_remove", {
        "user_id": "default", "item_id": task_id,
    })
    content = r["result"]["content"][0]["text"]
    assert "deleted" in content.lower()


@pytest.mark.asyncio
async def test_404_error(e2e_client, session_id):
    r = await call_tool(e2e_client, session_id, "tasks_modify", {
        "user_id": "default", "item_id": "nonexistent", "title": "Nope",
    })
    content = r["result"]["content"][0]["text"]
    assert "not found" in content.lower()


@pytest.mark.asyncio
async def test_pagination(e2e_client, session_id):
    for i in range(5):
        await call_tool(e2e_client, session_id, "tasks_capture", {
            "title": f"Item {i}", "type": "task",
        })

    r = await call_tool(e2e_client, session_id, "tasks_review", {
        "user_id": "default", "limit": 3, "offset": 0,
    })
    content = json.loads(r["result"]["content"][0]["text"])
    assert content["count"] == 3
    assert content["has_more"] is True


@pytest.mark.asyncio
async def test_user_isolation(e2e_client, session_id):
    await call_tool(e2e_client, session_id, "tasks_capture", {
        "title": "Alice item", "type": "task", "user_id": "alice",
    })
    r = await call_tool(e2e_client, session_id, "tasks_review", {"user_id": "bob"})
    content = json.loads(r["result"]["content"][0]["text"])
    assert content["total"] == 0


@pytest.mark.asyncio
async def test_markdown_format(e2e_client, session_id):
    await call_tool(e2e_client, session_id, "tasks_capture", {
        "title": "Test", "type": "task",
    })
    r = await call_tool(e2e_client, session_id, "tasks_review", {
        "user_id": "default", "response_format": "markdown",
    })
    content = r["result"]["content"][0]["text"]
    assert content.startswith("#")
