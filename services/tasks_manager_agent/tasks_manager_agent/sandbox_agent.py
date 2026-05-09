"""
SandboxAgent version — for Linux/macOS or Docker-based deployment.
When UnixLocalSandboxClient or DockerSandboxClient is available, use this
instead of the plain Agent in main.py.
"""
import asyncio

from agents import Runner
from agents.run import RunConfig
from agents.sandbox import SandboxAgent, SandboxRunConfig
from agents.sandbox.capabilities import Capabilities

from tasks_manager_agent.config import build_gemini_model

# Optional: Docker sandbox client (requires docker SDK)
# from agents.sandbox.sandboxes.docker import DockerSandboxClient, DockerSandboxClientOptions


def build_sandbox_agent() -> SandboxAgent:
    return SandboxAgent(
        name="Tasks Manager Agent",
        instructions="You are a helpful assistant. Respond concisely.",
        model=build_gemini_model(),
        capabilities=Capabilities.default(),
    )


async def main():
    agent = build_sandbox_agent()

    # UnixLocalSandboxClient requires macOS or Linux.
    # On Windows, use DockerSandboxClient with Docker Desktop running.
    import sys
    if sys.platform == "win32":
        # Uncomment and configure when Docker is available:
        # client = DockerSandboxClient()
        # options = DockerSandboxClientOptions(image="python:3.14-slim")
        # sandbox = SandboxRunConfig(client=client, options=options)
        raise RuntimeError(
            "SandboxAgent requires Docker on Windows. "
            "Start Docker Desktop, then use DockerSandboxClient."
        )
    else:
        from agents.sandbox.sandboxes.unix_local import UnixLocalSandboxClient
        client = UnixLocalSandboxClient()

    run_config = RunConfig(
        sandbox=SandboxRunConfig(client=client),
    )

    result = await Runner.run(
        agent,
        "Say hello world and tell me what tools you have available.",
        run_config=run_config,
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
