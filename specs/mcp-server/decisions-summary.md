# MCP Server Design Decisions

This document summarises every decision made for the `tasks_mcp` server before
writing code. Each entry lists the options considered, the one we locked, and
why.

---

## 1. Language

| Option | Description |
|---|---|
| **Python 3.12+** ✅ | Project default. FastMCP with Pydantic v2. Simple decorator-based tools, `uv` for deps. Lacks `structuredContent` but JSON string returns are sufficient. |
| TypeScript | Better MCP SDK maturity. `structuredContent` + `outputSchema` for typed agent responses. Requires separate runtime, build toolchain, and breaks project consistency. |

---

## 2. Transport

| Option | Description |
|---|---|
| **Streamable HTTP** ✅ | Session-based, multi-client, deployable on K8s. Port 8000 (configurable via `TASKS_MCP_PORT`), path `/mcp`. Health via MCP `tools/call` → `health`. Requires `initialize` handshake for `Mcp-Session-Id`. |
| stdio | Local-only, single client, subprocess model. Cannot run on K8s. |

---

## 3. Server Name

| Option | Description |
|---|---|
| **`tasks_mcp`** ✅ | Short, descriptive, follows `{service}_mcp` convention. Directory: `services/tasks_mcp/`, package: `tasks-mcp`. |
| `tm_mcp` | Cryptic — agents would not infer what it does. |
| `taskmanager_mcp` | Verbose — unnecessary typing with no benefit. |

---

## 4. Authentication

| Option | Description |
|---|---|
| **None** ✅ | No auth in v1. Revisit if the server is exposed beyond the internal cluster. |
| Token / mTLS / Pod identity | Premature — adds setup friction with no clear threat model yet. |

---

## 5. User Identity

| Option | Description |
|---|---|
| **Optional `user_id`, defaults to `"default"`** ✅ | Required for data scoping (otherwise `review_today` has no meaning). Agent passes from conversation context. No validation — pure string isolation. Keeps "no auth" intact. |
| Required auth-backed identity | Too heavy for v1. Would force auth before any tool can be used. |
| No user identity | Breaks every tool — no way to scope "today" or "my tasks" to a specific user. |

---

## 6. Tool Naming

| Option | Description |
|---|---|
| **`tasks_{intent}`** ✅ | Intent-based: `tasks_capture`, `tasks_review`, `tasks_modify`, `tasks_resolve`, `tasks_remove`. The verb is the intent, not the DB operation. |
| `tasks_{action}_{resource}` | Data-surface naming like `tasks_create_task`, `tasks_list_reminders`. Encourages domain-splitting (separate tools per entity type). |

---

## 7. Tool Granularity

| Option | Description |
|---|---|
| **5 intents** ✅ | Capture, review, modify, resolve, remove. Each maps to a complete human intent in a single call. No separate tools per entity type (task vs appointment vs reminder — just a `type` field). |
| CRUD per domain | 16+ tools that mirror database tables. Agents must compose multiple calls for simple user intents ("I finished the report" → find + update status). Poor agent ergonomics. |

---

## 8. Response Format

| Option | Description |
|---|---|
| **JSON (default) + Markdown** ✅ | `response_format` parameter on every data-returning tool. JSON for programmatic processing by agents, Markdown for human-readable display. Low cost — one shared formatter function. |
| JSON only | Agents parse well, but no human-readable fallback for debugging or display. |
| Markdown only | Human-friendly but forces agents to parse text for structured data. |

---

## 9. Tool Annotations

| Option | Description |
|---|---|
| **Required on every tool** ✅ | All four annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) declared on every tool. Default all-False — developer flips applicable ones. Enforced via code review. Prevents agents from misinterpreting tool safety. |
| Optional | Easy to forget. Missing annotations cause agents to guess — potentially auto-executing destructive operations. |

---

## 10. Error Handling

| Option | Description |
|---|---|
| **Uniform contract** ✅ | Single `_handle_api_error()` shared by all tools. Consistent format: `"Error: <what>. <what to try>."` Agents learn the pattern once. Easy to audit and update. |
| Per-tool | Inconsistent messages, harder to review, agents cannot rely on a predictable error format. |

---

## 11. Idempotency

| Option | Description |
|---|---|
| **Optional `idempotency_key` on all mutations** ✅ | UUID string. Server deduplicates within TTL window. Prevents duplicate task creation from retries or network issues. Aligns with constitutional requirement. |
| Not required | Safer to skip but violates idempotency principle. Retries could create duplicates. |

---

## 12. Pagination

| Option | Description |
|---|---|
| **Offset-based** ✅ | `limit` (default 20, max 100), `offset` (default 0). Returns `has_more`, `next_offset`, `total`. Simple, sufficient for our data volume. |
| Cursor-based | Better for live data with frequent inserts. Adds complexity (cursor encoding, ordering guarantees) not justified for v1. |

---

## 13. Resources

| Option | Description |
|---|---|
| **Tools only** ✅ | No MCP resources in v1. Everything is a tool. Resources add URI parsing and registration complexity with marginal benefit. Revisit if agents show frequent read-only lookup patterns. |
| Resources + Tools | Premature. Candidate URIs like `tasks:///task/{id}` can be added later without breaking changes. |

---

## 14. Project Structure

| Option | Description |
|---|---|
| **Domain modules** ✅ | `models/`, `tools/` (one file per intent), `client.py`, `errors.py`, `formatters.py`, `config.py`. Clean separation, easy to navigate, easy to test independently. |
| Flat (single file) | Fine for 3 tools, unmanageable for 5 intents + infrastructure + models in one file. |

---

## 15. Character Limit

| Option | Description |
|---|---|
| **25K chars, truncate with hint** ✅ | Prevents a single tool response from consuming the agent's entire context window. Includes `truncated: true` flag and `truncation_hint` with filter/pagination guidance. Relevant only for `tasks_review` with large result sets. |
| No limit | Risk of blowing the context. Inconsistent with our "context is the fundamental constraint" working practice. |

---

## 16. Evaluation

| Option | Description |
|---|---|
| **10 Q&A pairs, v1** ✅ | Read-only, independent, verifiable, stable questions covering all 5 intents. XML format per MCP guidelines. Ensures agents can effectively use the tools before shipping. |
| Defer | Violates "always verify" and "test-first" constitutional principles. |

---

## 17. Persistence

| Option | Description |
|---|---|
| **In-memory dict (`storage.py`)** ✅ | No external dependencies. Tools call `storage.create()`, `storage.list_items()`, etc. Shared `_idempotency` dict deduplicates within process lifecycle. `clear()` resets between tests. |
| External REST API via `client.py` | Original plan. Requires a running backend, adds deployment complexity, and couples tool layer to HTTP error semantics. Defers to future iteration. |

---

## 18. Health Probe

| Option | Description |
|---|---|
| **MCP `health` tool** ✅ | K8s probes call `tools/call` → `health` via `POST /mcp`. Consistent with the MCP protocol — no separate HTTP endpoint to maintain. |
| `GET /health` | Original plan. Adds an extra route outside the MCP protocol. Dockerfile HEALTHCHECK was implemented using the MCP approach. |

---

## 19. Time Format

| Option | Description |
|---|---|
| **UTC storage, agent translates** ✅ | Server stores/returns ISO 8601 UTC. Accepts optional IANA `timezone` param (e.g. `"America/New_York"`) for Markdown local-time rendering. Agent converts user's natural language time to UTC on input and UTC back to user timezone on display. |
| Server does all timezone handling | Server would need user timezone profiles and timezone math in every tool. Blurs responsibility — agent knows the user's context, not the server. |
