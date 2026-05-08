# AGENTS.md — Project Constitution

This repository builds an AI-native task management system using agents, tools,
APIs, and a user interface.

This file is the constitution for how we work: the principles, boundaries, and
operating rules that guide every design and implementation decision. Detailed
contracts belong in code, tests, schemas, and manifests.

---

## Product Direction

The product helps users manage tasks, reminders, and appointment-style workflows
through natural conversation. The Tasks Manager Agent is the primary
user-facing orchestrator. Other agents, tools, and services exist to support
that orchestrator, not to bypass it.

The system must remain:

* Clear enough for users to understand what action was taken.
* Reliable enough that task and notification changes are not duplicated.
* Explicit enough that time, date, identity, and destructive actions are never
  guessed.
* Modular enough that agents, tools, APIs, and UI layers can evolve separately.

---

## Agent Boundaries

* The Tasks Manager Agent owns user intent, clarification, routing, and final
  confirmation.
* Task mutations must go through the Tasks MCP server.
* Booking workflows must be routed to the Appointment Booking Agent.
* The Appointment Booking Agent must not mutate tasks directly.
* Notifications are triggered only after a valid task mutation succeeds.
* Destructive actions require user confirmation before execution.
* Missing or ambiguous dates, times, participants, or targets must be clarified
  before action is taken.

---

## Tech Stack Defaults

These are the defaults for any new service, agent, or tool in this repo.
Deviating requires a clear operational reason.

* **Preferred programming language:** Python 3.12+.
* **Package and environment manager:** `uv`. Use `uv` for dependency
  resolution, virtual environments, lockfiles, and running scripts. Do not mix
  `pip`, `poetry`, or `conda` into the same service unless there is a
  documented reason.

---

## Project Layout Decisions

* **Image Registry:** GitHub Container Registry (ghcr.io). Public images since
  the repo is public.
* **Kubernetes Manifests:** All K8s manifests and Helm charts go into
  `/deployments` in the project root.
* **Dockerfiles:** Every service's Dockerfile lives at its service root
  (e.g. `services/tasks_mcp/Dockerfile`). No top-level Dockerfile.

---

## Engineering Principles

* **Cloud Native by default.** Every decision must avoid cloud vendor lock-in.
  The system must be deployable anywhere — self-hosted, bare metal, any cloud
  provider — without architectural changes.
* **LLM-agnostic.** The system must not depend on any specific LLM or provider.
  Every interface must work with any LLM through standard protocols (MCP, API).
  Inference is a pluggable component, not a hard dependency.
* **Test-first by default.** Start with a failing test that captures the
  expected behavior, implement the smallest useful change, then refactor.
* **Prefer simple, explicit designs** over clever abstractions.
* **Keep changes small** enough to review and reason about.
* **Preserve clear separation** between orchestration, tools, APIs,
  persistence, notifications, authentication, and UI.
* **Make failures visible and recoverable** instead of silent.
* **Design every mutation to be idempotent** where practical.
* **Treat time, timezone, retries, and duplicate requests** as first-class
  product concerns.
* **Avoid direct database changes** from agents or UI code when a service
  exists.
* **Do not introduce a new framework, SDK, queue, database, or runtime
  dependency** without a clear operational reason.
* **Check official documentation** before using any SDK, framework, or
  platform feature. Use agent skills or MCP tools to access docs. Outdated
  assumptions are treated as bugs.

---

## Development Workflow

1. Understand the user-facing behavior and the system boundary involved.
2. Read the existing code before designing the change.
3. Check official docs for any SDK, framework, or platform behavior using
   agent skills or MCP tools.
4. Write or update tests first when the behavior is testable.
5. Implement the smallest coherent change.
6. Run tests, type checks, linters, and local service checks.
7. Review the Kubernetes and operational impact before considering the work
   done.

---

## Kubernetes-First Mindset

The system will be deployed on Kubernetes. Every decision — from service
boundaries to dependency choices — accounts for this from the start.

Services must be designed for:

* Stateless application containers.
* Configuration through environment variables and mounted secrets.
* Health checks, graceful shutdown, and safe handling of interrupted requests.
* Horizontal scaling without duplicate task mutations or notifications.
* Idempotent jobs, retries, and scheduled work.
* Structured logs and correlation IDs for debugging.
* Safe database migrations during deployment.
* Internal communication through stable service names.

---

## Observability

The system must make agent and service behavior inspectable. Log important
decisions and tool calls with correlation IDs. Track task mutations, booking
handoffs, notification scheduling, retries, failures, and user confirmation
boundaries. Logs must not leak secrets, credentials, or personal data.

---

## Quality Gates

Before completing work, verify the relevant layer:

* Agent behavior: intent parsing, clarification, routing, confirmations.
* MCP tools: validation, deterministic responses, idempotency.
* Notifications: scheduling, cancellation, retry behavior, duplicate
  prevention.
* API layer: auth, validation, error handling, observability.
* UI layer: accessible flows, loading/error/empty states.
* Deployment: configuration, secrets, probes, scaling, rollback.

If a check cannot be run locally, document what was not verified and why.

---

## Always Verify

Verification is not a final step — it is part of doing the work. Before
declaring something done, prove it works. Trust nothing by default. Verify
both the happy path and at least one failure or edge case. Treat unverified
claims the same as bugs.

Give agents tools to verify their own work — tests, type checks, linters,
health checks, MCP tools, hooks, browser automation — because quality comes
from feedback loops, not hope. When an agent has a verification loop, the
quality of the final result improves dramatically.

---

## Working Practices

### Treat context as the fundamental constraint

The context window holds the entire conversation: every message, every file
read, every command output. Performance degrades as context fills. Every
practice below exists to manage this constraint. When in doubt, reset.

### Plan before executing

For any non-trivial change, produce a written plan first. Iterate until it is
solid before touching code. When execution goes wrong, stop and re-plan.
Invite review before committing.

Use separate sessions for writing and reviewing — a fresh reviewer context
catches blind spots the original author missed. Have one agent write the plan
and a second review it with a critical eye before any code is written.

### Use parallel workstreams

Run multiple isolated sessions instead of overloading one. Each session is a
separate context window. Use separate directories or git worktrees to keep
workstreams isolated. Name sessions descriptively so they can be resumed
later. Start with 2-3 parallel sessions, not 15.

### Delegate investigations to subagents

When research requires reading many files, delegate to a subagent instead of
loading everything into the main context. The subagent explores in its own
context and reports back findings. Keep the main context clean for the actual
work.

### Write self-evolving rules

When a mistake is made, update AGENTS.md so the error is not repeated. Use
the pattern: after a correction, tell the agent "Update your AGENTS.md so you
don't make that mistake again." Agents are effective at writing rules for
themselves. Prune rules the codebase already enforces.

### Automate repeated workflows

If a workflow is done more than once a day, turn it into a skill or script.
Build a session-end review skill that summarizes decisions, open questions,
follow-ups, and insights worth capturing. Run it before closing any session
while context is fresh.

### Give Claude the problem, not the solution

Describe the outcome you want rather than prescribing exact steps. Agents
often find better approaches when given freedom to investigate. Do not
micromanage.

### Use a learning output style

Configure the agent to explain the *why* behind its changes instead of just
the *what*. This builds shared understanding, especially when working with
unfamiliar code, libraries, or patterns. Generate visual walkthroughs or
diagrams for complex systems.

### Manage sessions aggressively

* Clear context between unrelated tasks. Long sessions with irrelevant
  content degrade performance.
* After two failed corrections on the same issue, stop and restart with a
  clearer prompt rather than spiraling.
* Use session rewind to recover from wrong turns rather than pushing through.
* Abandoning a session is normal — some fraction of sessions hit unexpected
  scenarios and starting fresh beats recovering a confused one.
* End every session with a review to capture insights before they are lost.

### Avoid common failure patterns

* **Kitchen-sink sessions**: do not pile unrelated questions into one
  context. Reset between tasks.
* **Correction spirals**: more than two failed corrections means the
  approach is muddled — stop and re-plan.
* **Over-specified rules**: if the agent already follows a rule, delete it.
  Keep instructions lean enough that important rules are not ignored.
* **Trust-then-verify gap**: plausible output is not verified output. Edge
  cases are not optional.
* **Infinite exploration**: scope investigations narrowly or delegate them
  to subagents.

---

## Final Principle

Keep this file minimal, explicit, and operational. If guidance can be
enforced by tests or inferred from code, it does not belong here.
