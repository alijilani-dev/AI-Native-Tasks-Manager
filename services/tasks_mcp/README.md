# tasks_mcp

MCP server for AI-native task management — exposes task, appointment, and
reminder management tools to LLM agents via the [Model Context Protocol](https://modelcontextprotocol.io).

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package and environment manager)

## Quick Start

```bash
cd services/tasks_mcp
uv sync          # install dependencies
uv run python -m tasks_mcp.server   # start server on http://localhost:8000
```

The server listens on `http://localhost:8000/mcp`. Port can be overridden with
the `TASKS_MCP_PORT` environment variable.

## Development

```bash
# Run all unit tests (93 tests)
uv run pytest tasks_mcp/tests/ -v

# Run end-to-end tests (requires running server)
uv run pytest tasks_mcp/e2e/ -v -m e2e

# Lint check
uv run ruff check tasks_mcp/

# Type check
uv run mypy tasks_mcp/ --exclude 'tasks_mcp/tests/'
```

## Docker

```bash
# Build the production image (multi-stage)
docker build -t tasks-mcp:prod -f services/tasks_mcp/Dockerfile services/tasks_mcp/

# Run
docker run -d --name tasks-mcp -p 8000:8000 tasks-mcp:prod
```

The image includes a health check that calls the MCP `health` tool via the
`tasks_mcp/healthcheck.py` script.

## CI/CD

GitHub Actions workflow at `.github/workflows/tasks-mcp.yml`:

| Event | Trigger | Jobs |
|-------|---------|------|
| Push to `main` | Changes to `services/tasks_mcp/**` | `check` (lint + typecheck + test) → `build-and-push` (Docker → ghcr.io) |
| Pull request | Changes to `services/tasks_mcp/**` | `check` only |

Published image:
`ghcr.io/alijilani-dev/ai-native-tasks-manager/tasks-mcp:latest`

## MCP Tools Reference

| Tool | ReadOnly | Destructive | Idempotent | Description |
|------|----------|-------------|------------|-------------|
| `health` | Yes | No | No | K8s probe — returns `{"status": "ok"}` |
| `tasks_capture` | No | No | Yes | Create any work item (task/appointment/reminder) |
| `tasks_review` | Yes | No | Yes | Query with filters, pagination, JSON or markdown |
| `tasks_modify` | No | No | Yes | Update any field(s) on an existing item |
| `tasks_resolve` | No | No | Yes | Set terminal status (completed/cancelled/skipped) |
| `tasks_remove` | No | Yes | Yes | Permanently delete a work item |

## Connecting OpenCode

See [`services/tasks_mcp_connection_summary.md`](../tasks_mcp_connection_summary.md)
for instructions on connecting this server to OpenCode.
