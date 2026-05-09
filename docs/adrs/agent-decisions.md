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
guardrails, structured outputs, sessions, and sandbox agent support — all
primitives we need.

**Consequences:**
- Positive: MCP servers connect natively via `MCPServerStreamableHttp`.
- Positive: Guardrails enforce clarification and confirmation rules.
- Positive: Sessions provide built-in conversation state persistence.
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
from agents import ModelSettings
from agents.mcp import MCPServerStreamableHttp
from agents.run import RunConfig
from agents.sandbox import (
    SandboxAgent,
    Capabilities,
)
from agents.sandbox.sandboxes.docker import DockerSandboxClient

agent = SandboxAgent(
    name="Tasks Manager Agent",
    instructions=SKILL.md_content,
    model="gemini-2.5-flash-lite-preview",
    mcp_servers=[MCPServerStreamableHttp(params={"url": "http://tasks-mcp:8000/mcp"})],
    default_manifest=Manifest(
        entries={
            "workspace": Dir(),
        }
    ),
    capabilities=Capabilities.default(),
)
```

The agent receives the Tasks Manager Agent skill as instructions, connects to
tasks_mcp via `MCPServerStreamableHttp`, and runs inside a sandboxed workspace.

**Reasons:**
- The tasks_mcp server encapsulates all task mutation logic — no need for
  multiple agents owning different subsets of tools.
- The `SandboxAgent` workspace provides a persistent filesystem for artifacts,
  temporary files, and possible future skill execution.
- Simpler to build, test, deploy, and debug than a multi-agent handoff topology.
- Routing to the Appointment Booking Agent (future) can be added via handoff
  or `agent.as_tool()` without architectural changes.

**Consequences:**
- Positive: Single code path — one agent, one runner, one set of guardrails.
- Positive: Sandbox workspace gives us flexibility for future capabilities.
- Positive: Scales to multi-agent later via handoffs without rewriting.
- Negative: All 6 MCP tools + sandbox capabilities are visible to the LLM
  simultaneously (tool annotations guide selection).

---

## Decision 3: Use SandboxAgent (not plain Agent)

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The OpenAI Agents SDK provides `SandboxAgent` — an agent primitive with a
persistent filesystem workspace, shell access, file editing, and sandbox
lifecycle management. We evaluated whether this is appropriate for the
Tasks Manager Agent, initially concluding it was not. After further review,
the decision was revisited and reversed.

**Decision:**
Use **`SandboxAgent`** (not plain `Agent`).

**Reasons for reversal:**
- The sandbox workspace gives the agent a persistent filesystem for artifact
  storage, exported task lists, notification scripts, and skill execution.
- Sandbox capabilities (Filesystem, Shell, Skills, Memory) enable future
  extensibility without rewriting the agent.
- The sandbox lifecycle (create, resume, snapshot, cleanup) maps well to
  our Kubernetes deployment model — each user session gets an isolated workspace.
- The overhead is acceptable: minimal manifest, default capabilities, and a
  sandbox client (UnixLocal for dev, Docker/hosted for production).

**Consequences:**
- Positive: Persistent workspace for artifacts and temporary files.
- Positive: Sandbox capabilities available for future use (skills, memory).
- Positive: Session isolation — each user gets their own workspace.
- Neutral: Requires sandbox client infrastructure (Docker or hosted provider).
- Negative: Additional complexity in deployment (sandbox lifecycle, manifests).

---

## Decision 4: Model Selection — Gemini 2.5 Flash Lite Preview + OpenAI

**Date:** 2026-05-09

**Status:** Accepted

**Context:**
The system must be LLM-agnostic per project constitution. We need an initial
model that balances cost, speed, and capability for task management workflows.
Gemini 2.5 Flash Lite Preview is a fast, cost-effective model with function
calling support.

**Decision:**
Start with **`gemini-2.5-flash-lite-preview`** as the default model. Support
OpenAI models as an alternative for higher-quality responses when needed.

Gemini is integrated via the Chat Completions-compatible endpoint:

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

agent = SandboxAgent(
    name="Tasks Manager Agent",
    instructions=SKILL.md_content,
    model=model,
    ...
)
```

**Gemini compatibility with SandboxAgent:**
- Gemini 2.5 Flash Lite supports function/tool calling, which is how
  SandboxAgent capabilities (Filesystem, Shell, MCP) are exposed to the LLM.
- The Chat Completions API shape is sufficient — sandbox capabilities use
  standard function tools, not Responses-specific features.
- Structured outputs work via JSON mode (not strict schema).
- OpenAI models can be swapped in later via `RunConfig(model="gpt-5.5")`
  for higher-quality responses without code changes.

**Consequences:**
- Positive: Cost-effective — Gemini 2.5 Flash Lite is significantly cheaper than GPT.
- Positive: Fast inference — suitable for real-time conversational workflows.
- Positive: LLM-agnostic by design — swapping models requires changing only the model parameter.
- Negative: Chat Completions API lacks some Responses-only features (tool search, namespaces).
- Negative: OpenAI tracing disabled — must use custom trace processor for observability.
- Neutral: Gemini integrates via OpenAI-compatible endpoint — no third-party adapter needed.

---

## Decision 5: Sandbox Client — Docker for Development, Hosted for Production

**Date:** 2026-05-09

**Status:** Draft

**Context:**
SandboxAgent requires a sandbox client that provisions the isolated workspace.
For local development, a lightweight client suffices. For production on Kubernetes,
we need a client that works in containerized environments.

**Decision:**
- **Development:** `UnixLocalSandboxClient` for macOS/Linux, or
  `DockerSandboxClient` for consistent local parity.
- **Production:** `DockerSandboxClient` (self-hosted on K8s) or a hosted
  provider (E2B, Modal, etc.) depending on operational requirements.

```python
# Development
run_config = RunConfig(
    sandbox=SandboxRunConfig(
        client=UnixLocalSandboxClient(),
    ),
)

# Production (Docker on K8s)
from agents.sandbox.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions

run_config = RunConfig(
    sandbox=SandboxRunConfig(
        client=DockerSandboxClient(),
        options=DockerSandboxClientOptions(image="tasks-manager-sandbox:latest"),
    ),
)
```

**Open questions:**
- What base image should the sandbox use? Minimal Python image?
- Should we use Docker-in-K8s or a hosted provider for production?
- How do we handle sandbox session persistence across user conversations?
- What snapshot strategy do we use (local vs remote)?

**Next steps:**
1. Prototype with `UnixLocalSandboxClient` locally
2. Define the sandbox manifest (workspace structure, files)
3. Test Gemini function calling with sandbox capabilities
4. Evaluate Docker vs hosted sandbox providers for production
5. Design session lifecycle (create → resume → snapshot → cleanup)

---

## Decision 6: Connected Service — Tasks Manager Agent Service

**Date:** 2026-05-09

**Status:** Draft

**Context:**
The Tasks Manager Agent needs to run as a service that accepts user input and
produces responses. It connects to the tasks_mcp MCP server. The architecture
must be cloud-native and deployable on Kubernetes.

**Open questions:**
- Should the agent run as an HTTP API (FastAPI) or an MCP server itself?
- How should sessions be persisted (SQLAlchemySession, RedisSession)?
- How does the Appointment Booking Agent get discovered and routed to?
- What is the notification triggering contract?
- How does sandbox session state get persisted across service restarts?

**Next steps:**
1. Design the service interface (HTTP API vs MCP server)
2. Choose session persistence backend
3. Define the Appointment Booking Agent handoff contract
4. Design notification trigger flow
5. Write the full implementation spec
