# MCP Server: Implementation Guide

> **Note:** This document was updated after implementation to reflect actual
> decisions made during development. Key departures from the original plan are
> noted inline. The most significant change: **in-memory `storage.py` replaced
> the external API client pattern** — tools call storage directly instead of
> going through `httpx` to a REST backend. The `client.py` module still exists
> for future use but is not wired into any tool.

This document maps mcp-builder skill patterns onto our specific project files.
Follow strictly — each step includes the test to write first (TDD), the code
pattern from the skill, and how it maps to our decisions.

---

## Step 1: Scaffold with UV

### Tests to write first

```python
# tests/test_server.py
def test_server_imports():
    """Server module loads without errors."""
    from tasks_mcp.server import mcp
    assert mcp.name == "tasks_mcp"

def test_health_response():
    """GET /health returns 200."""
    # via httpx against running server
```

### Implementation

```bash
mkdir -p services/tasks_mcp/tasks_mcp/tests
cd services/tasks_mcp
uv init --package
uv add mcp pydantic httpx
uv add --dev pytest pytest-asyncio ruff
```

**`services/tasks_mcp/tasks_mcp/mcp_instance.py`** — decoupled FastMCP instance for testability:

```python
from mcp.server.fastmcp import FastMCP
from tasks_mcp.config import PORT

mcp = FastMCP("tasks_mcp", host="0.0.0.0", port=PORT, streamable_http_path="/mcp")
```

**`services/tasks_mcp/tasks_mcp/server.py`** — imports tools and runs:

```python
import tasks_mcp.tools.capture  # noqa: F401
import tasks_mcp.tools.modify    # noqa: F401
import tasks_mcp.tools.remove    # noqa: F401
import tasks_mcp.tools.resolve   # noqa: F401
import tasks_mcp.tools.review    # noqa: F401
from tasks_mcp.mcp_instance import mcp

@mcp.tool()
async def health() -> str:
    '''Health check for K8s probes. Returns ok when server is running.'''
    return '{"status": "ok"}'

def main():
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
```

**`services/tasks_mcp/pyproject.toml`**:

```toml
[project]
name = "tasks-mcp"
version = "0.1.0"
description = "MCP server for AI-native task management"
requires-python = ">=3.12"
dependencies = [
    "mcp",
    "pydantic>=2.0",
    "httpx",
]

[project.scripts]
tasks-mcp = "tasks_mcp.server:main"

[tool.ruff]
line-length = 120
target-version = "py312"
src = ["."]

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]

[tool.ruff.lint.isort]
known-first-party = ["tasks_mcp"]

[tool.mypy]
python_version = "3.12"
strict = false
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = false
ignore_missing_imports = true
exclude = [
    "tasks_mcp/tests/",
    ".venv/",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tasks_mcp/tests"]
markers = [
    "e2e: end-to-end integration tests (start server, call tools via HTTP)",
]

[dependency-groups]
dev = [
    "mypy>=1.20.2",
    "pytest>=9.0.3",
    "pytest-asyncio>=1.3.0",
    "ruff>=0.15.12",
]
```

---

## Step 2: Shared Infrastructure

### 2a. Storage (in-memory)

> **Architectural change from original plan.** The original plan called for an
> external REST API accessed via `client.py`. During implementation, we chose
> in-memory `storage.py` to eliminate the external dependency. The tool layer
> calls `storage` functions directly. `client.py` is kept for future REST
> backend migration.

**`tasks_mcp/storage.py`** — in-memory dict with CRUD, filtering, pagination, idempotency:

```python
_store: dict[str, dict] = {}
_idempotency: dict[str, dict] = {}

def create(user_id, data, idempotency_key=None) -> dict
def get(item_id) -> dict | None
def list_items(user_id, ...filters..., limit=20, offset=0) -> dict
def update(item_id, user_id, data, idempotency_key=None) -> dict | None
def resolve(item_id, user_id, status, note=None, idempotency_key=None) -> dict | None
def delete(item_id, user_id, idempotency_key=None) -> bool
def clear() -> None   # test helper
```

### 2b. Config

**Test**: assert `LIMIT_DEFAULT == 20`, `LIMIT_MAX == 100`, `CHAR_LIMIT == 25000`

**`tasks_mcp/config.py`**:

```python
import os

PORT = int(os.environ.get("TASKS_MCP_PORT", "8000"))
LIMIT_DEFAULT = 20
LIMIT_MAX = 100
LIMIT_MIN = 1
CHAR_LIMIT = 25000
USER_ID_DEFAULT = "default"
```

### 2c. Errors — per skill `_handle_api_error()` pattern

**Test to write first**:

```python
# tests/test_errors.py
def test_404_error():
    result = handle_api_error(HTTPStatusError(response=Mock(status_code=404)))
    assert "not found" in result.lower()

def test_403_error():
    result = handle_api_error(HTTPStatusError(response=Mock(status_code=403)))
    assert "permission" in result.lower()

def test_429_error():
    result = handle_api_error(HTTPStatusError(response=Mock(status_code=429)))
    assert "rate limit" in result.lower()

def test_timeout_error():
    result = handle_api_error(TimeoutException())
    assert "timed out" in result.lower()
```

**`tasks_mcp/errors.py`** — exact pattern from skill reference (`python_mcp_server.md` lines 212-225):

```python
import httpx

def handle_api_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Error: Item not found. Check the item_id and try again."
        elif e.response.status_code == 403:
            return "Error: Permission denied. You don't have access to this resource."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded. Wait before making more requests."
        return f"Error: API request failed with status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    return f"Error: Unexpected error: {type(e).__name__}"
```

### 2d. Formatters — per skill JSON/Markdown pattern

**Test to write first**:

```python
# tests/test_formatters.py
def test_format_json_returns_structured():
    result = format_json(items, total=5, offset=0)
    assert '"items"' in result
    assert '"total": 5' in result

def test_format_markdown_has_headers():
    result = format_markdown(items, total=5, offset=0)
    assert result.startswith("#")

def test_truncation_at_limit():
    long_items = [{"data": "x" * 5000}] * 100
    result, truncated = enforce_char_limit(json.dumps(long_items), limit=1000)
    assert truncated is True

def test_timezone_conversion_in_markdown():
    """Timestamps render in supplied timezone."""
    result = format_markdown(items_with_dates, timezone="America/New_York")
    assert "EST" in result or "EDT" in result
```

**`tasks_mcp/formatters.py`** — build two functions:

```python
import json
from datetime import datetime, timezone
from config import CHAR_LIMIT

def format_json(items: list, total: int, offset: int, limit: int) -> str:
    """Structured JSON with pagination metadata."""
    response = {
        "total": total,
        "count": len(items),
        "offset": offset,
        "has_more": total > offset + len(items),
        "next_offset": offset + len(items) if total > offset + len(items) else None,
        "items": items,
    }
    return json.dumps(response, indent=2, default=str)

def format_markdown(
    items: list,
    total: int,
    offset: int,
    limit: int,
    timezone: str | None = None,
    title: str = "Results",
) -> str:
    """Human-readable markdown with optional timezone-aware timestamps."""
    lines = [f"# {title}", "", f"Found {total} items (showing {len(items)})", ""]
    for item in items:
        lines.append(f"## {item.get('title', 'Untitled')} ({item.get('id', '?')})")
        for key, value in item.items():
            if key in ("id", "title"):
                continue
            if key.endswith("_at") or key.endswith("_time"):
                value = _format_timestamp(value, timezone)
            lines.append(f"- **{key}**: {value}")
        lines.append("")
    return "\n".join(lines)

def _format_timestamp(ts: str, tz: str | None = None) -> str:
    """Convert UTC ISO string to readable format, optionally in IANA timezone."""
    from datetime import datetime
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if tz:
        import zoneinfo
        dt = dt.astimezone(zoneinfo.ZoneInfo(tz))
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def enforce_char_limit(text: str, limit: int = CHAR_LIMIT):
    """Truncate text at limit, return (text, was_truncated)."""
    if len(text) <= limit:
        return text, False
    return text[:limit] + f'\n\n[Truncated at {limit} chars. Use limit/offset or add filters to narrow results.]', True
```

### 2e. Client — per skill httpx pattern (unused in v1)

**Test to write first**:

```python
# tests/test_client.py
@pytest.mark.asyncio
async def test_client_get_success():
    """Client can GET and return parsed JSON."""
    # mock httpx, assert response parsed

@pytest.mark.asyncio
async def test_client_get_wraps_errors():
    """Non-200 responses go through handle_api_error."""
    # mock httpx to return 404, assert error raised
```

**`tasks_mcp/client.py`** — per skill pattern (`python_mcp_server.md` lines 232-244):

```python
import httpx
from config import PORT

API_BASE = f"http://localhost:{PORT}"

async def api_request(
    endpoint: str,
    method: str = "GET",
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method,
            f"{API_BASE}/{endpoint}",
            json=json_data,
            params=params,
        )
        response.raise_for_status()
        return response.json()
```

---

## Step 3: Model — per skill Pydantic pattern

**Test to write first**:

```python
# tests/test_models.py
def test_create_input_valid():
    """Valid WorkItemCreateInput passes validation."""
    data = WorkItemCreateInput(
        title="Call mom",
        type="task",
        due_date="2026-05-07T15:00:00Z",
    )
    assert data.title == "Call mom"

def test_create_input_invalid_type():
    """Invalid type raises validation error."""
    with pytest.raises(ValidationError):
        WorkItemCreateInput(title="Bad", type="invalid_type")

def test_create_input_strips_whitespace():
    """Pydantic ConfigDict strips whitespace."""
    data = WorkItemCreateInput(title="  hello  ", type="task")
    assert data.title == "hello"

def test_create_input_forbids_extra():
    """Extra fields are rejected."""
    with pytest.raises(ValidationError):
        WorkItemCreateInput(title="Test", type="task", unknown_field="x")

def test_update_input_all_partial():
    """All fields optional for partial update."""
    data = WorkItemUpdateInput()
    assert data.model_dump(exclude_none=True) == {}
```

**`tasks_mcp/models/work_item.py`** — per skill Pydantic v2 pattern (`python_mcp_server.md` lines 73-118):

```python
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ItemType(str, Enum):
    TASK = "task"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"


class ItemStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class WorkItemCreateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(..., description="Work item title", min_length=1, max_length=500)
    type: ItemType = Field(..., description="Item type: task, appointment, or reminder")
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[int] = Field(default=None, ge=1, le=5, description="Priority 1 (highest) to 5 (lowest)")
    due_date: Optional[str] = Field(default=None, description="ISO 8601 UTC due date")
    reminder_at: Optional[str] = Field(default=None, description="ISO 8601 UTC reminder trigger time")
    start_time: Optional[str] = Field(default=None, description="ISO 8601 UTC start (appointments)")
    end_time: Optional[str] = Field(default=None, description="ISO 8601 UTC end (appointments)")
    location: Optional[str] = Field(default=None, max_length=500, description="Physical or virtual location")
    participants: Optional[list[str]] = Field(default=None, description="Participant identifiers")
    idempotency_key: Optional[str] = Field(default=None, description="UUID for deduplication")


class WorkItemUpdateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    due_date: Optional[str] = Field(default=None)
    reminder_at: Optional[str] = Field(default=None)
    start_time: Optional[str] = Field(default=None)
    end_time: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=500)
    participants: Optional[list[str]] = Field(default=None)
    idempotency_key: Optional[str] = Field(default=None)


class WorkItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    type: ItemType
    status: ItemStatus
    description: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[str] = None
    reminder_at: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[list[str]] = None
    created_at: str
    updated_at: str
```

---

## Step 4: Tools — Capture

**Test to write first**:

```python
# tests/tools/test_capture.py
@pytest.mark.asyncio
async def test_capture_task():
    """tasks_capture creates a task and returns it."""
    result = await tasks_capture(title="Buy milk", type="task")
    assert "id" in result
    assert result["title"] == "Buy milk"

@pytest.mark.asyncio
async def test_capture_appointment():
    """tasks_capture creates an appointment with time fields."""
    result = await tasks_capture(
        title="Dentist", type="appointment",
        start_time="2026-05-10T14:00:00Z", end_time="2026-05-10T15:00:00Z",
    )
    assert result["type"] == "appointment"
    assert result["start_time"] == "2026-05-10T14:00:00Z"

@pytest.mark.asyncio
async def test_capture_default_user_id():
    """Missing user_id defaults to 'default'."""
    result = await tasks_capture(title="Test", type="task")
    assert result["user_id"] == "default"

@pytest.mark.asyncio
async def test_capture_idempotency():
    """Same idempotency_key returns same result."""
    result1 = await tasks_capture(title="Dup", type="task", idempotency_key="abc-123")
    result2 = await tasks_capture(title="Dup", type="task", idempotency_key="abc-123")
    assert result1["id"] == result2["id"]
```

**`tasks_mcp/tools/capture.py`** — calls `storage.create()` directly instead of `api_request()`:

```python
import json
from mcp.types import ToolAnnotations
from tasks_mcp.errors import handle_api_error
from tasks_mcp.mcp_instance import mcp
from tasks_mcp.storage import create

@mcp.tool(
    name="tasks_capture",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def tasks_capture(
    title: str,
    type: str,
    user_id: str = "default",
    description: str | None = None,
    priority: int | None = None,
    due_date: str | None = None,
    reminder_at: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    location: str | None = None,
    participants: list[str] | None = None,
    idempotency_key: str | None = None,
) -> str:
    '''Create any work item — task, appointment, or reminder — in one call.

    Accepts all fields for all item types. The `type` field determines which
    fields are relevant. Returns the created item with its assigned ID.

    Args:
        title: Item title (e.g. 'Call mom', 'Dentist appointment')
        type: "task", "appointment", or "reminder"
        user_id: User identifier for data scoping (default: "default")
        description: Optional detailed notes
        priority: 1 (highest) to 5 (lowest)
        due_date: ISO 8601 UTC due date
        reminder_at: ISO 8601 UTC reminder trigger time
        start_time: ISO 8601 UTC start time (appointments)
        end_time: ISO 8601 UTC end time (appointments)
        location: Physical or virtual location
        participants: List of participant identifiers
        idempotency_key: UUID for deduplication

    Returns:
        JSON string of the created work item.
    '''
    try:
        data = create(user_id, {
            "title": title, "type": type, "description": description,
            "priority": priority, "due_date": due_date, "reminder_at": reminder_at,
            "start_time": start_time, "end_time": end_time, "location": location,
            "participants": participants,
        }, idempotency_key)
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return handle_api_error(e)
```

Repeat the same TDD pattern for the remaining 4 tools:

---

## Step 5: Tools — Review (calls `storage.list_items()`)

**Tests**: filter by status, date range, search text, type, priority, overdue flag; pagination boundary; empty results; character truncation; `timezone` param in markdown mode; `response_format` switch.

**`tasks_mcp/tools/review.py`** — `@mcp.tool(name="tasks_review")` with `readOnlyHint=True`:

```python
async def tasks_review(
    user_id: str = "default",
    status: str | None = None,
    type: str | None = None,
    search_text: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    is_overdue: bool | None = None,
    priority: int | None = None,
    limit: int = 20,
    offset: int = 0,
    response_format: str = "json",
    timezone: str | None = None,
) -> str:
    data = list_items(user_id=user_id, status=status, item_type=type, ...)
    if response_format == "markdown":
        return format_markdown(items, ...)
    return format_json(items, ...)
```

---

## Step 6: Tools — Modify (calls `storage.update()`)

**Tests**: partial update preserves unset fields; update title + reschedule in one call; unknown item_id returns 404 error; idempotency dedup.

**`tasks_mcp/tools/modify.py`** — `@mcp.tool(name="tasks_modify")`:

```python
async def tasks_modify(user_id: str, item_id: str, title=None, ...) -> str:
    body = {k: v for k, v in locals().items() if v is not None and k not in ("user_id", "item_id")}
    result = update(item_id, user_id, body, idempotency_key)
    if result is None:
        return "Error: Item not found. Check the item_id and try again."
    return json.dumps(result, indent=2, default=str)
```

---

## Step 7: Tools — Resolve (calls `storage.resolve()`)

**Tests**: complete → status changes to completed; cancel → status changes to cancelled; unknown item_id returns 404.

**`tasks_mcp/tools/resolve.py`** — `@mcp.tool(name="tasks_resolve")`:

```python
async def tasks_resolve(user_id: str, item_id: str, status: str, note=None, idempotency_key=None) -> str:
    result = resolve(item_id, user_id, status, note, idempotency_key)
    if result is None:
        return "Error: Item not found. Check the item_id and try again."
    return json.dumps(result, indent=2, default=str)
```

---

## Step 8: Tools — Remove (calls `storage.delete()`)

> **Note:** The original plan specified a `confirm` parameter. The actual
> implementation omits `confirm` — the `destructiveHint=True` annotation and
> the constitution requirement for user confirmation at the agent level are
> sufficient.

**Tests**: delete existing item → removed; delete non-existent → returns false; wrong user → returns false; idempotency key dedup.

**`tasks_mcp/tools/remove.py`** — `@mcp.tool(name="tasks_remove", destructiveHint=True)`:

```python
async def tasks_remove(user_id: str, item_id: str, idempotency_key=None) -> str:
    success = delete(item_id, user_id, idempotency_key)
    if not success:
        return "Error: Item not found. Check the item_id and try again."
    return json.dumps({"deleted": True, "id": item_id}, indent=2)
```

---

## Step 9: Wire Tools into Server

The actual implementation uses a side-effect import pattern. Tool modules
import `mcp` from `mcp_instance.py` and register themselves via `@mcp.tool()`
at import time. The server simply imports all tool modules to trigger
registration.

**`tasks_mcp/server.py`**:

```python
import tasks_mcp.tools.capture  # noqa: F401  — registers tasks_capture
import tasks_mcp.tools.modify   # noqa: F401  — registers tasks_modify
import tasks_mcp.tools.remove   # noqa: F401  — registers tasks_remove
import tasks_mcp.tools.resolve  # noqa: F401  — registers tasks_resolve
import tasks_mcp.tools.review   # noqa: F401  — registers tasks_review
from tasks_mcp.mcp_instance import mcp

@mcp.tool()
async def health() -> str:
    return '{"status": "ok"}'

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

---

## Step 10: End-to-End Human Scenario Tests

Write a shell script or pytest integration test that runs the full server and exercises these real user flows:

| Scenario | Steps | Verifies |
|---|---|---|
| **Morning routine** | capture "Buy groceries" with priority 3 → review today → capture "Call dentist" as appointment with time → review today shows 2 items | Multi-tool workflow |
| **Reschedule** | capture "Team standup" as appointment → modify its time → review shows updated time | Modify correctness |
| **Completion** | capture "Write report" → resolve as completed → review with status=pending excludes it | Status filtering |
| **Reminder flow** | capture "Pay bills" with reminder_at → review shows reminder field | Reminder in line |
| **Cleanup** | capture "Temp note" → remove it → review returns empty | Delete + confirmation |
| **Pagination** | capture 25 items → review with limit=10 → check has_more → get next page → check offset=10 | Offset pagination |
| **Idempotent retry** | capture with idempotency_key → call again with same key → same ID returned | Dedup |
| **Timezone display** | capture with due_date in UTC → review with timezone="America/New_York" in markdown mode → timestamp in local time | Timezone conversion |
| **User isolation** | capture as user "alice" → review as user "bob" → bob sees 0 items | user_id scoping |
| **Error recovery** | review with invalid status → meaningful error message | Error contract |

---

## Step 11: Run & Verify

```bash
cd services/tasks_mcp
uv run pytest tasks_mcp/tests/ -v           # All TDD tests pass (93 tests)
uv run ruff check tasks_mcp/                # Lint clean
uv run mypy tasks_mcp/ --exclude 'tasks_mcp/tests/'  # Type check
uv run python -m tasks_mcp.server &         # Start server on :8000
# Run end-to-end scenarios against running server
# (See .github/workflows/tasks-mcp.yml for CI pipeline)
```

---

## File Tree (Actual)

```
services/tasks_mcp/
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── tasks_mcp/
│   ├── __init__.py
│   ├── server.py                    # Entry point: health tool + main()
│   ├── mcp_instance.py              # FastMCP instance (decoupled for testing)
│   ├── storage.py                   # In-memory dict storage (not in original plan)
│   ├── config.py                    # Constants + TASKS_MCP_PORT env var
│   ├── client.py                    # httpx client (unused in v1, kept for future)
│   ├── errors.py                    # handle_api_error() — primarily catch-all
│   ├── formatters.py                # format_json + format_markdown
│   ├── models/
│   │   ├── __init__.py
│   │   └── work_item.py             # WorkItemCreateInput, WorkItemUpdateInput, WorkItemResponse
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── capture.py               # tasks_capture → storage.create()
│   │   ├── review.py                # tasks_review → storage.list_items()
│   │   ├── modify.py                # tasks_modify → storage.update()
│   │   ├── resolve.py               # tasks_resolve → storage.resolve()
│   │   └── remove.py                # tasks_remove → storage.delete()
│   ├── e2e/                         # Integration tests (not in original plan)
│   │   ├── __init__.py
│   │   ├── conftest.py              # Server lifecycle + session fixtures
│   │   └── test_e2e.py              # 10 end-to-end test scenarios
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py              # Autouse storage reset
│       ├── test_server.py           # 4 tests: name, health, tool registration
│       ├── test_config.py           # 6 tests: port, limits, defaults
│       ├── test_errors.py           # 6 tests: 404, 403, 429, timeout, etc.
│       ├── test_formatters.py       # 5 tests: JSON, markdown, truncation
│       ├── test_client.py           # 2 tests: mocked httpx calls
│       ├── test_models.py           # 11 tests: validation, enum, constraints
│       ├── test_storage.py          # 17 tests: CRUD, idempotency, isolation
│       ├── e2e_scenarios.py         # Standalone scenario runner (not in original plan)
│       └── tools/
│           ├── __init__.py
│           ├── test_capture.py      # 5 tests
│           ├── test_review.py       # 10 tests
│           ├── test_modify.py       # 7 tests
│           ├── test_resolve.py      # 5 tests
│           └── test_remove.py       # 3 tests
└── .github/workflows/tasks-mcp.yml  # CI: lint, type-check, test (not in original plan)
```
