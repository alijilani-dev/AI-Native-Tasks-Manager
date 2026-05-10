"""
SandboxAgent version — for Linux/macOS or Docker-based deployment.
When UnixLocalSandboxClient or DockerSandboxClient is available, use this
instead of the plain Agent in main.py.
"""
import asyncio
import sys

from agents import Runner
from agents.run import RunConfig
from agents.sandbox import SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import Capabilities

from tasks_manager_agent.config import build_failover_model


def build_sandbox_agent() -> SandboxAgent:
    return SandboxAgent(
        name="Tasks Manager Agent",
        instructions="You are a helpful assistant. Respond concisely.",
        model=build_failover_model(),
        capabilities=Capabilities.default(),
    )


async def main():
    agent = build_sandbox_agent()

    if sys.platform == "win32":
        raise RuntimeError(
            "SandboxAgent requires Docker on Windows. "
            "Start Docker Desktop, then use DockerSandboxClient."
        )

    from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient

    run_config = RunConfig(
        sandbox=SandboxRunConfig(client=UnixLocalSandboxClient()),
    )

    result = await Runner.run(
        agent,
        "Say hello world and tell me what tools you have available.",
        run_config=run_config,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
