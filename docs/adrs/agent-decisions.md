# Agent Architecture Decisions

## Decision 1: Agent Framework — OpenAI Agents SDK

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The Tasks Manager Agent needs an agent framework to orchestrate user interactions,
route intents, enforce safety rules, and call the tasks_mcp MCP server.

**Decision:**
Use the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) as
the agent framework. It provides first-class MCP server integration, handoffs,
guardrails, structured outputs, sessions, and sandbox agent support.

**Consequences:**
- Positive: MCP servers connect natively via `MCPServerStreamableHttp`.
- Positive: Guardrails enforce clarification and confirmation rules.
- Positive: `SandboxAgent` gives us a persistent workspace.
- Negative: Adds a Python dependency (`openai-agents`) to the service.

---

## Decision 2: Orchestration Pattern — Single SandboxAgent (Option A)

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The SDK offers two orchestration patterns: (A) a single agent with MCP tools,
and (B) a triage agent with handoffs to specialist agents.

**Decision:**
Use **Option A — single `SandboxAgent` with MCP tools**.

```python
agent = SandboxAgent(
    name="Tasks Manager Agent",
    instructions=SKILL.md_content,
    model=FailoverModel(primary=Gemini, secondary=OpenAI),
    mcp_servers=[MCPServerStreamableHttp(url="http://tasks-mcp:8000/mcp")],
    default_manifest=Manifest(entries={"workspace": Dir()}),
    capabilities=Capabilities.default(),
)
```

**Consequences:**
- Positive: Single code path — one agent, one runner.
- Positive: Sandbox workspace for artifacts, logs, and script execution.
- Positive: Scales to multi-agent later via handoffs.

---

## Decision 3: Use SandboxAgent

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
`SandboxAgent` provides a persistent filesystem workspace, shell access, file
editing, and sandbox lifecycle management via sandbox clients.

**Decision:**
Use `SandboxAgent`. Locally requires Docker on Windows (`DockerSandboxClient`)
or `UnixLocalSandboxClient` on Linux/macOS.

**Stack:**
- `SandboxAgent` — agent definition with `default_manifest` + `capabilities`
- `Manifest` — workspace contract (files, dirs, repos)
- `Capabilities.default()` — `Filesystem`, `Shell`, `Compaction`
- `SandboxRunConfig(client=DockerSandboxClient(...))` — per-run sandbox session

**Consequences:**
- Positive: Persistent workspace for task exports, notification scripts, etc.
- Positive: Session isolation per user.
- Negative: Requires Docker on Windows for local development.

---

## Decision 4: Model Selection — Failover (Gemini Primary + OpenAI Secondary)

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The system must be LLM-agnostic. We need a failover mechanism so if the primary
model provider fails, the secondary takes over without user-visible errors.

**Decision:**
Use a `FailoverModel` that wraps two `OpenAIChatCompletionsModel` instances:

| Role | Provider | Configured via |
|------|----------|----------------|
| Primary | Gemini | `TASKS_AGENT_PRIMARY_MODEL` + `TASKS_AGENT_PRIMARY_API_KEY` |
| Secondary | OpenAI | `TASKS_AGENT_SECONDARY_MODEL` + `TASKS_AGENT_SECONDARY_API_KEY` |

On any exception from the primary, the secondary is called automatically.
Tracing is sent to the OpenAI Traces dashboard via `set_tracing_export_api_key()`
using the secondary API key.

**Consequences:**
- Positive: Transparent failover — no user-visible errors.
- Positive: Tracing works for both stacks via OpenAI dashboard.
- Negative: Traces show "model not found" for Gemini calls (expected — Gemini
  model names don't exist on OpenAI).

---

## Decision 5: Development Approach — Step by Step

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
First time using the OpenAI Agents SDK. We build incrementally.

**Decision:**
Build in stages: project scaffold → hello world model test → SandboxAgent with
MCP → full SKILL.md instructions.

All secrets stored in `.env` loaded via `python-dotenv`. Production secret
strategy deferred.

**Consequences:**
- Positive: Validates each layer before moving to the next.
- Positive: Catches framework-specific issues early.
