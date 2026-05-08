# MCP Server: Decisions

| # | Decision | Locked Value | Notes |
|---|---|---|---|---|
| 1 | **Language** | Python 3.12+ | Consistent with project stack. FastMCP with Pydantic v2. |
| 2 | **Transport** | Streamable HTTP | Port 8000 (configurable via `TASKS_MCP_PORT`), path `/mcp`. Health via MCP tool, not `GET /health`. Requires `initialize` handshake for session. |
| 3 | **Server Name** | `tasks_mcp` | Package: `tasks-mcp`, directory: `services/tasks_mcp/` |
| 4 | **Auth** | None | No authentication for v1. Revisit if needed. |
| 4a | **User Identity** | Optional `user_id`, defaults to `"default"` | Scopes data per user. Agent passes from conversation context. No validation — string identifier only. |
| 5 | **Tool Naming** | `tasks_{intent}` | Intent-based, not data-surface. E.g. `tasks_capture`, `tasks_review`, `tasks_modify` |
| 6 | **Tool Granularity** | 5 intents | capture, review, modify, resolve, remove. No separate CRUD per domain. |
| 7 | **Response Format** | JSON (default) + Markdown | `response_format` parameter on every data-returning tool. JSON for programmatic, Markdown for human-readable. |
| 8 | **Tool Annotations** | Required on every tool | `ToolAnnotations` dataclass from `mcp.types`. All-False default, developer flips applicable ones. |
| 9 | **Error Handling** | Uniform contract | `handle_api_error()` shared across all tools. Structured: `Error: <what>. <what to try>.` Errors are text content in result, not protocol-level errors. |
| 10 | **Idempotency** | Optional `idempotency_key` (UUID) on all mutating tools | Passed in body. Server deduplicates within process lifetime via `_idempotency` dict. |
| 11 | **Pagination** | Offset-based | Default `limit=20`, max `limit=100`. Return `has_more`, `next_offset`, `total`. |
| 12 | **Resources** | Tools only | No MCP resources in v1. Revisit if agents show frequent read-only lookup patterns. |
| 13 | **Project Structure** | Domain modules | `models/`, `tools/`, `storage.py`, `mcp_instance.py`, `errors.py`, `formatters.py` |
| 14 | **Character Limit** | 25K chars | Truncate responses exceeding limit. Append truncation hint. |
| 15 | **Evaluation** | 10 Q&A pairs covering core workflow | Created as part of v1. Read-only, independent, verifiable questions. |
| 16 | **Time Format** | UTC storage, agent translates | Server stores/returns UTC. Accepts optional `timezone` param (IANA, e.g. `"America/New_York"`) for Markdown formatting. Agent converts user times to UTC on input and UTC to user times on display. |
| 17 | **Persistence** | In-memory dict (`storage.py`) | No external database for v1. `_store` and `_idempotency` dicts. Future: swap `storage.py` with DB backend without touching tool layer. |
