# MCP Server: Design

## Overview

`tasks_mcp` is a Python MCP server that exposes task, reminder, and appointment management tools to LLM agents via the Model Context Protocol. It runs as a Streamable HTTP service on Kubernetes, with no authentication in v1.

## Design Principle

Tools are organized by **human intent**, not by database entity. There are 5 intents that cover all user actions: capture, review, modify, resolve, remove. Each tool is a complete end-to-end operation — the agent expresses what the user wants to happen, and the server handles the schema internally.

---

## Architecture

```
┌──────────────┐     Streamable HTTP      ┌──────────────────┐
│  Agent       │ ◄──────────────────────► │  tasks_mcp       │
│  (MCP client)│     POST /mcp            │  FastMCP server  │
└──────────────┘                          │  :8000           │
                                          │                  │
                                          │  Health via:     │
                                          │  tools/call      │
                                          │  → health        │
                                          └────────┬─────────┘
                                                   │
                                                   ▼
                                          ┌──────────────────┐
                                          │  storage.py      │
                                          │  (in-memory)     │
                                          └──────────────────┘
```

---

## Server Initialization

```python
# mcp_instance.py — created separately for testability
mcp = FastMCP("tasks_mcp", host="0.0.0.0", port=PORT, streamable_http_path="/mcp")

# server.py — entry point
@mcp.tool()
async def health() -> str:
    return '{"status": "ok"}'

mcp.run(transport="streamable-http")
```

---

## Transport

| Item | Value |
|---|---|---|
| Protocol | Streamable HTTP |
| Endpoint | `POST /mcp` |
| Port | 8000 (configurable via `TASKS_MCP_PORT`) |
| Probe | `tools/call` → `health` via MCP (`POST /mcp`) |
| Session | `initialize` handshake required; `Mcp-Session-Id` header on subsequent calls |

---

## Common Parameters

Every tool accepts `user_id` (string, optional, defaults to `"default"`) for data scoping. No auth validation — pure identifier for multi-user isolation.

---

## Tool Design Principles

1. **Intent-based**: tools map to what a human wants to do, not to database operations
2. **End-to-end**: each tool is a complete operation, not a step in a multi-call workflow
3. **Unified model**: task, appointment, reminder are just a `type` field on a work item — the agent doesn't need separate tools for each
4. **Annotations on every tool**: readOnlyHint, destructiveHint, idempotentHint, openWorldHint
5. **Input validation**: Pydantic v2 with `Field(description=..., constraints...)`
6. **Output**: JSON by default, Markdown on request
7. **Uniform error handling**: single `_handle_api_error()` for all tools
8. **Idempotency**: optional `idempotency_key` on mutations
9. **Pagination**: offset-based on `tasks_review`
10. **Character limit**: 25K truncation with filter hint
11. **Time handling**: UTC internally. Agent translates user timezone ↔ UTC. Optional `timezone` param on tools for Markdown formatting in user's local time.

---

## Project Structure

```
services/tasks_mcp/
├── server.py                  # Entry point: imports tools, defines health, calls mcp.run()
├── mcp_instance.py            # FastMCP instance creation (decoupled for testing)
├── storage.py                 # In-memory dict storage (replaces external API)
├── models/
│   ├── __init__.py
│   └── work_item.py           # Unified work item model (task/appointment/reminder)
├── tools/
│   ├── __init__.py
│   ├── capture.py             # tasks_capture
│   ├── review.py              # tasks_review
│   ├── modify.py              # tasks_modify
│   ├── resolve.py             # tasks_resolve
│   └── remove.py              # tasks_remove
├── client.py                  # Persistence client (httpx) — unused; kept for future REST backend
├── errors.py                  # _handle_api_error() uniform contract
├── formatters.py              # JSON + Markdown response builders
├── config.py                  # Constants, env vars
├── e2e/                       # End-to-end pytest suite (session-scoped server fixture)
│   ├── __init__.py
│   ├── conftest.py
│   └── test_e2e.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Autouse storage reset
│   ├── test_server.py
│   ├── test_config.py
│   ├── test_client.py
│   ├── test_errors.py
│   ├── test_formatters.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── e2e_scenarios.py       # Standalone scenario runner (no server lifecycle)
│   └── tools/
│       ├── __init__.py
│       ├── test_capture.py
│       ├── test_review.py
│       ├── test_modify.py
│       ├── test_resolve.py
│       └── test_remove.py
├── pyproject.toml
├── Dockerfile
└── uv.lock
```

---

## Evaluation

10 Q&A pairs covering all 5 intents. Read-only, independent, verifiable, stable. Stored in XML format per MCP evaluation guidelines.

---

## Dependencies

- `mcp` (Python SDK with FastMCP)
- `pydantic` v2
- `httpx` (async HTTP client, for future REST backend)
- `uuid` (stdlib)
- `zoneinfo` (stdlib, for timezone-aware Markdown timestamps)

## Persistence Strategy

**In-memory dictionary (`storage.py`)** — v1 uses an in-memory `dict` for simplicity.
- No external database or REST dependency.
- Shared idempotency store (`_idempotency`) prevents duplicate mutations within the process lifetime.
- `storage.clear()` resets both stores between test runs.
- Future iterations can replace `storage.py` with a database backend without changing the tool layer.
