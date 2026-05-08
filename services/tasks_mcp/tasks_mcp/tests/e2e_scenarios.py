#!/usr/bin/env python3
"""End-to-end scenario tests for tasks_mcp.

Run against a running server:
    uv run python -m tasks_mcp.server &
    uv run python tests/e2e_scenarios.py
"""

import json
import urllib.error
import urllib.request

BASE = "http://localhost:8000/mcp"


def call_tool(name: str, args: dict) -> dict:
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": args},
    }).encode()
    req = urllib.request.Request(
        BASE,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def assert_ok(result: dict, label: str):
    assert "result" in result, f"[FAIL] {label}: no result — {result}"
    print(f"  [PASS] {label}")


def assert_contains(result: dict, key: str, label: str):
    content = result["result"]["content"][0]["text"]
    assert key in content, f"[FAIL] {label}: '{key}' not in response"
    print(f"  [PASS] {label}")


def run_scenarios():
    print("\n=== E2E: Morning Routine ===")
    r = call_tool("tasks_capture", {"title": "Buy groceries", "type": "task", "priority": 3})
    assert_ok(r, "capture task")
    task_id = json.loads(r["result"]["content"][0]["text"])["id"]

    r = call_tool("tasks_capture", {
        "title": "Call dentist", "type": "appointment",
        "start_time": "2026-05-07T14:00:00Z", "end_time": "2026-05-07T15:00:00Z",
    })
    assert_ok(r, "capture appointment")

    r = call_tool("tasks_review", {"user_id": "default"})
    assert_contains(r, task_id, "review shows captured task")

    print("\n=== E2E: Modify ===")
    r = call_tool("tasks_modify", {
        "user_id": "default", "item_id": task_id,
        "title": "Buy groceries and snacks",
    })
    assert_contains(r, "Buy groceries and snacks", "modify title")

    print("\n=== E2E: Resolve ===")
    r = call_tool("tasks_resolve", {
        "user_id": "default", "item_id": task_id, "status": "completed",
    })
    assert_contains(r, "completed", "resolve as completed")

    r = call_tool("tasks_review", {"user_id": "default", "status": "pending"})
    content = r["result"]["content"][0]["text"]
    assert task_id not in content, "[FAIL] completed item still in pending view"
    print("  [PASS] completed item excluded from pending")

    print("\n=== E2E: Pagination ===")
    for i in range(25):
        call_tool("tasks_capture", {"title": f"Bulk item {i}", "type": "task"})
    r = call_tool("tasks_review", {"user_id": "default", "limit": 10, "offset": 0})
    content = r["result"]["content"][0]["text"]
    data = json.loads(content)
    assert data["count"] == 10, f"[FAIL] expected 10 items, got {data['count']}"
    assert data["has_more"] is True, "[FAIL] expected has_more=True"
    print("  [PASS] pagination returns 10 with has_more")

    print("\n=== E2E: Remove ===")
    r = call_tool("tasks_capture", {"title": "Temp note", "type": "task"})
    temp_id = json.loads(r["result"]["content"][0]["text"])["id"]
    r = call_tool("tasks_remove", {"user_id": "default", "item_id": temp_id})
    assert_contains(r, "deleted", "remove item")

    print("\n=== E2E: User Isolation ===")
    call_tool("tasks_capture", {"title": "Alice item", "type": "task", "user_id": "alice"})
    r = call_tool("tasks_review", {"user_id": "bob"})
    content = r["result"]["content"][0]["text"]
    assert "Alice item" not in content, "[FAIL] bob sees alice's item"
    print("  [PASS] user isolation works")

    print("\n=== E2E: Error Handling ===")
    r = call_tool("tasks_modify", {"user_id": "default", "item_id": "nonexistent", "title": "Nope"})
    content = r["result"]["content"][0]["text"]
    assert "not found" in content.lower(), f"[FAIL] expected 'not found', got: {content}"
    print("  [PASS] 404 returns uniform error")

    print("\n=== E2E: Markdown Format ===")
    r = call_tool("tasks_review", {"user_id": "default", "response_format": "markdown"})
    content = r["result"]["content"][0]["text"]
    assert content.startswith("#"), "[FAIL] markdown should start with #"
    print("  [PASS] markdown format returns headers")

    print("\n" + "=" * 40)
    print("ALL E2E SCENARIOS PASSED")
    print("=" * 40)


if __name__ == "__main__":
    run_scenarios()
