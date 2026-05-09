import asyncio
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

from tasks_manager_agent.config import build_model

SKILL_PATH = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "tasks-manager" / "SKILL.md"


def load_instructions() -> str:
    """Load the Tasks Manager Agent instructions from SKILL.md."""
    # Strip YAML frontmatter (--- ... ---)
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, body = text.partition("---")
        _, _, body = body.partition("---")
        return body.strip()
    return text.strip()


async def main():
    instructions = load_instructions()

    async with MCPServerStreamableHttp(
        name="Tasks MCP Server",
        params={
            "url": "http://localhost:8000/mcp",
            "timeout": 10,
        },
        cache_tools_list=True,
    ) as mcp_server:
        agent = Agent(
            name="Tasks Manager Agent",
            instructions=instructions,
            model=build_model(),
            mcp_servers=[mcp_server],
        )

        result = await Runner.run(
            agent,
            "Create a task called 'Buy groceries' with priority 3 and due date tomorrow.",
        )
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
