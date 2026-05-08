# Connecting OpenCode to tasks_mcp via MCP Protocol

## Overview

[OpenCode](https://opencode.ai) is an open-source AI coding agent that supports
adding external tools via the **Model Context Protocol (MCP)**. Our
`tasks_mcp` server exposes 6 tools (`health`, `tasks_capture`,
`tasks_review`, `tasks_modify`, `tasks_resolve`, `tasks_remove`) over
Streamable HTTP.

Once connected, the LLM can read, create, update, resolve, and delete work
items directly through natural conversation.

---

## Prerequisites

- [OpenCode](https://opencode.ai) installed (`npm install -g opencode-ai` or
  `brew install anomalyco/tap/opencode`)
- `tasks_mcp` server running (or able to start it)

---

## Step 1: Start the Server

```bash
cd services/tasks_mcp
uv run python -m tasks_mcp.server
```

The server listens on `http://localhost:8000` with the MCP endpoint at
`/mcp`. Port can be overridden with `TASKS_MCP_PORT`.

---

## Step 2: Add MCP Configuration

Add the following to your OpenCode config (`opencode.jsonc` in the project
root, or `~/.config/opencode/config.jsonc`):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "tasks_mcp": {
      "type": "remote",
      "url": "http://localhost:8000/mcp",
      "enabled": true,
      "timeout": 10000
    }
  }
}
```

Since the server runs locally without authentication, no `headers` or `oauth`
is needed.

### Alternative: Local Mode (stdio)

You can also run the server as a subprocess managed by OpenCode:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "tasks_mcp": {
      "type": "local",
      "command": ["uv", "run", "python", "-m", "tasks_mcp.server"],
      "enabled": true,
      "timeout": 10000
    }
  }
}
```

---

## Step 3: Verify Connection

```bash
opencode mcp list
```

Expected output shows all 6 registered tools:

| Tool | Description |
|------|-------------|
| `health` | Health check for K8s probes |
| `tasks_capture` | Create any work item (task, appointment, reminder) |
| `tasks_review` | Query work items with filters and pagination |
| `tasks_modify` | Update fields on an existing work item |
| `tasks_resolve` | Set a terminal status (completed, cancelled, skipped) |
| `tasks_remove` | Permanently delete a work item |

---

## Step 4: Use in Prompts

Tools are automatically available to the LLM. Example prompts:

> "Use tasks_capture to remind me to buy groceries tomorrow at 5pm"
>
> "What's on my plate today? Use tasks_review"
>
> "Mark the dentist appointment as completed via tasks_resolve"

To make tool usage automatic, add to your project's `AGENTS.md`:

```
When managing tasks, appointments, or reminders, use `tasks_mcp` tools.
```

---

## Connection Modes Summary

| Mode | `type` | How Server Runs | Best For |
|------|--------|-----------------|----------|
| **Remote** | `"remote"` | Already running on localhost | Development, persistent server |
| **Local** | `"local"` | OpenCode spawns as subprocess | Ephemeral, per-session usage |
| **Remote + OAuth** | `"remote"` | Deployed on a remote host | Production / cloud deployment |

Our server uses Streamable HTTP transport, so **remote mode** is the natural
fit for local development.

---

## Troubleshooting

- **Server not reachable**: Ensure `tasks_mcp` is running on the expected
  port. Check with a health tool call (see Dockerfile HEALTHCHECK for the
  correct request format).
- **"Not Acceptable" error**: The Accept header must include both
  `application/json` and `text/event-stream`. Most MCP clients handle this
  automatically; manual `curl`/`Invoke-WebRequest` calls need explicit
  `Accept: application/json, text/event-stream`.
- **"Missing session ID" error**: Streamable HTTP requires an `initialize`
  handshake first. The server returns an `Mcp-Session-Id` header on the
  `initialize` response; include it on all subsequent requests.
- **Tools not showing up**: Run `opencode mcp list` to check status. Verify
  the `url` includes `/mcp`.
- **Timeout errors**: Increase `timeout` in the config (default 5000ms).
- **Context too large**: Disable the MCP server when not needed by setting
  `"enabled": false` or using `"tools": { "tasks_mcp_*": false }`.
