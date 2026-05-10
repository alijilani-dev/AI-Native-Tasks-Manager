"""Tasks Manager Agent — SandboxAgent with Gemini+OpenAI failover and tasks_mcp MCP."""

import asyncio
import os
import sys
from pathlib import Path

from agents import Runner
from agents.mcp import MCPServerStreamableHttp
from agents.run import RunConfig
from agents.sandbox import (
    Manifest,
    SandboxAgent,
    SandboxRunConfig,
)
from agents.sandbox.capabilities import Capabilities
from agents.sandbox.entries import Dir

from tasks_manager_agent.config import build_failover_model

SKILL_PATH = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "tasks-manager" / "SKILL.md"


def load_instructions() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, body = text.partition("---")
        _, _, body = body.partition("---")
        return body.strip()
    return text.strip()


def build_sandbox_client():
    """Return the appropriate sandbox client for the current platform."""
    if sys.platform == "win32":
        from agents.sandbox.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions

        docker_host = os.environ.get("DOCKER_HOST")
        return DockerSandboxClient(
            docker_client_kwargs={"base_url": docker_host} if docker_host else {},
        ), DockerSandboxClientOptions(image="python:3.14-slim")

    from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient

    return UnixLocalSandboxClient(), None


async def main():
    instructions = load_instructions()

    async with MCPServerStreamableHttp(
        name="Tasks MCP Server",
        params={"url": "http://localhost:8000/mcp", "timeout": 10},
        cache_tools_list=True,
    ) as mcp_server:
        agent = SandboxAgent(
            name="Tasks Manager Agent",
            instructions=instructions,
            model=build_failover_model(),
            mcp_servers=[mcp_server],
            default_manifest=Manifest(
                entries={
                    "workspace": Dir(),
                },
            ),
            capabilities=Capabilities.default(),
        )

        client, options = build_sandbox_client()
        sandbox_config = SandboxRunConfig(client=client, options=options)
        run_config = RunConfig(sandbox=sandbox_config)

        result = await Runner.run(
            agent,
            "Create a task called 'Buy groceries' with priority 3 and due date tomorrow.",
            run_config=run_config,
        )
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
