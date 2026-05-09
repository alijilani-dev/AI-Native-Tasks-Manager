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
and (B) a triage agent with handoffs to specialist agents. The system also has
an Appointment Booking Agent (future) and notification triggers.

**Decision:**
Use **Option A — single `SandboxAgent` with MCP tools**.

```python
agent = SandboxAgent(
    name="Tasks Manager Agent",
    instructions=SKILL.md_content,
    model=model,
    mcp_servers=[MCPServerStreamableHttp(params={"url": "http://localhost:8000/mcp"})],
    capabilities=Capabilities.default(),
)
```

**Reasons:**
- tasks_mcp encapsulates all task mutation logic — no need for multiple agents.
- The `SandboxAgent` workspace provides a persistent filesystem for artifacts.
- Simpler to build, test, and debug than multi-agent handoff topology.
- Routing to the Appointment Booking Agent (future) can be added later.

**Consequences:**
- Positive: Single code path — one agent, one runner.
- Positive: Sandbox workspace gives flexibility for future capabilities.
- Positive: Scales to multi-agent later via handoffs without rewriting.

---

## Decision 3: Use SandboxAgent (not plain Agent)

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The OpenAI Agents SDK provides `SandboxAgent` — an agent primitive with a
persistent filesystem workspace, shell access, file editing, and sandbox
lifecycle management.

**Decision:**
Use **`SandboxAgent`** (not plain `Agent`).

**Reasons:**
- Persistent workspace for artifact storage, exported task lists, scripts.
- Sandbox capabilities (Filesystem, Shell, Memory) enable future extensibility.
- Session isolation — each user gets their own workspace.

**Consequences:**
- Positive: Persistent workspace for artifacts and temporary files.
- Positive: Session isolation.
- Neutral: Requires sandbox client (UnixLocalSandboxClient for local dev).

---

## Decision 4: Model Selection — Gemini 2.5 Flash Lite Preview

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The system must be LLM-agnostic per project constitution. We need an initial
model that balances cost, speed, and capability for task management workflows.

**Decision:**
Start with **`gemini-2.5-flash-lite-preview`** via OpenAI-compatible endpoint.
OpenAI models can be swapped in later for higher quality when needed.

```python
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, set_tracing_disabled

set_tracing_disabled(True)

client = AsyncOpenAI(
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash-lite-preview",
    openai_client=client,
)
```

**Consequences:**
- Positive: Cost-effective and fast.
- Positive: LLM-agnostic — swapping models requires changing only the model parameter.
- Negative: Chat Completions API lacks some Responses-only features.
- Negative: OpenAI tracing disabled — must use custom processor or disable.

---

## Decision 5: Development Approach — Step by Step

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
First time using the OpenAI Agents SDK. Rather than designing everything upfront,
we build incrementally to validate each layer works. Local development is on
Windows where `UnixLocalSandboxClient` is unavailable, so we use plain `Agent`
locally and `SandboxAgent` on Linux deployment targets.

**Decision:**
Build in stages: project scaffold → hello world agent → connect MCP → full SKILL.md instructions.

**Phase 1:** Create project with `uv`, install `openai-agents`, `python-dotenv`.
Verify a minimal `Agent` runs with Gemini.

**Phase 2:** Connect to tasks_mcp via `MCPServerStreamableHttp`. Verify tools are
discoverable and callable.

**Phase 3:** Load SKILL.md content as agent instructions. Test full task management
workflows.

**Local vs Production:**
- **Local (Windows):** Plain `Agent` — works cross-platform, no sandbox dependency.
- **Production (Linux/K8s):** `SandboxAgent` with `DockerSandboxClient` or hosted
  provider. Sandbox version is scaffolded at `tasks_manager_agent/sandbox_agent.py`.
- Both use the same model, instructions, and MCP server — switching requires only
  changing the agent class and run config.

All secrets stored in `.env` loaded via `python-dotenv`. Production secret
strategy (K8s Secrets, etc.) deferred.

**Consequences:**
- Positive: Validates each layer before moving to the next.
- Positive: Catches framework-specific issues early.
- Positive: Same SKILL.md instructions work for both Agent and SandboxAgent.
- Negative: Need to validate SandboxAgent separately on Linux.
