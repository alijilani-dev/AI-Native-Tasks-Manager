# Agent Architecture Decisions

## Decision 1: Agent Framework — OpenAI Agents SDK

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The Tasks Manager Agent needs an agent framework to orchestrate user interactions,
route intents, enforce safety rules, and call the tasks_mcp MCP server. Several
options were considered, including building directly on the MCP protocol or using
a general-purpose LLM framework.

**Decision:**
Use the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) as
the agent framework. It provides first-class MCP server integration, handoffs,
guardrails, structured outputs, and session management — all primitives we need.

**Consequences:**
- Positive: MCP servers connect natively via `MCPServerStreamableHttp` — no adapter layer needed.
- Positive: Guardrails enforce clarification and confirmation rules without custom code.
- Positive: Sessions provide built-in conversation state persistence.
- Positive: The SDK is LLM-agnostic — can swap models via `model` parameter.
- Neutral: Binds to the SDK's agent model (Agent + Runner) rather than raw MCP.
- Negative: Adds a Python dependency (`openai-agents`) to the service.

---

## Decision 2: Orchestration Pattern — Single Agent (Option A)

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The SDK offers two orchestration patterns: (A) a single agent with MCP tools,
and (B) a triage agent with handoffs to specialist agents. The system also has
an Appointment Booking Agent (future) and Notification triggers.

**Decision:**
Use **Option A — single Agent with MCP tools** as the primary architecture.

```python
agent = Agent(
    name="Tasks Manager Agent",
    instructions=SKILL.md_content,
    mcp_servers=[MCPServerStreamableHttp(params={"url": "http://localhost:8000/mcp"})],
)
```

The agent receives the Tasks Manager Agent skill (`.agents/skills/tasks-manager/SKILL.md`)
as its instructions, and connects to tasks_mcp via `MCPServerStreamableHttp`. All
6 MCP tools are available for the LLM to call.

**Reasons:**
- The tasks_mcp server already encapsulates all task mutation logic — no need for
  multiple agents to own different subsets of tools.
- The SKILL.md already defines the agent's behavior (intent parsing, clarification,
  confirmation, routing) — the instructions parameter is the natural home for it.
- Simpler to build, test, deploy, and debug than a multi-agent handoff topology.
- Routing to the Appointment Booking Agent (future) can be handled via a handoff
  or an `agent.as_tool()` when that component exists — no architectural change needed.

**Consequences:**
- Positive: Single code path — one agent, one runner, one set of guardrails.
- Positive: Easy to iterate on instructions by editing SKILL.md.
- Positive: Scales to multi-agent later via handoffs without rewriting the agent.
- Neutral: All 6 tools are visible to the LLM simultaneously (tool annotations
  help guide selection).
- Negative: Not using the SDK's multi-agent orchestration — leaves that flexibility
  on the table if we later need it.

---

## Decision 3: Against SandboxAgent

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The OpenAI Agents SDK recently added `SandboxAgent` — an agent primitive that
provides a persistent filesystem workspace, shell access, file editing, and
sandbox lifecycle management. We evaluated whether this is appropriate for the
Tasks Manager Agent.

**Decision:**
Do **not** use `SandboxAgent`. Use plain `Agent` instead.

**Reasons:**
- The Tasks Manager Agent is an **API-centric orchestrator** — it calls MCP tools,
  not shell commands or file operations.
- Adopting SandboxAgent would require provisioning containers/VMs per session,
  managing sandbox lifecycle, and paying for compute/storage we don't need.
- SandboxAgent is in **beta**; plain Agent is production-stable (GA).
- If we later need workspace-centric workflows (e.g., a coding agent that clones
  repos and runs tests), we can introduce SandboxAgent for that specific use case
  without changing the Tasks Manager Agent.

**Consequences:**
- Positive: No infrastructure overhead beyond the tasks_mcp server.
- Positive: Lighter weight — the agent runs in a simple Python process.
- Positive: No sandbox lifecycle to manage (create, snapshot, resume, cleanup).
- Negative: We cannot use sandbox-native capabilities (filesystem, shell, skills)
  — but we don't need them for task management.

---

## Decision 4: Connected Service — Tasks Manager Agent Service

**Date:** 2026-05-09

**Status:** Draft

**Context:**
The Tasks Manager Agent needs to run as a service that accepts user input and
produces responses. It connects to the tasks_mcp MCP server. The architecture
must be cloud-native, stateless, and deployable on Kubernetes per the project
constitution.

**Open questions:**
- Should the agent run as an HTTP API (FastAPI) or an MCP server itself?
- How should sessions be persisted (SQLite, Redis, PostgreSQL)?
- How does the Appointment Booking Agent get discovered and routed to?
- What is the notification triggering contract?

**Next steps:**
1. Research session persistence backends (SQLAlchemySession, RedisSession, etc.)
2. Design the service interface (HTTP vs MCP)
3. Define the Appointment Booking Agent handoff contract
4. Design the notification trigger flow
5. Write the full spec
