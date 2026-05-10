"""Test all tasks_mcp tools one by one through the agent."""

import asyncio
from pathlib import Path

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

from tasks_manager_agent.config import build_failover_model

SKILL_PATH = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "tasks-manager" / "SKILL.md"


def load_instructions() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, _, body = text.partition("---")
        _, _, body = body.partition("---")
        return body.strip()
    return text.strip()


TESTS = [
    ("health", "Check if the system is healthy. Call the health tool."),
    ("capture", "Create a task called 'Test task from agent' with priority 2."),
    ("review", "List all tasks. Call tasks_review with response_format='markdown'."),
    ("capture_appointment", "Create an appointment called 'Team standup' for tomorrow at 9am."),
    ("capture_reminder", "Create a reminder called 'Water plants' for today at 6pm."),
    ("review_all", "Review all work items and tell me how many there are."),
    ("modify", "Find the task called 'Test task from agent' and change its priority to 1."),
    ("resolve", "Find the task called 'Test task from agent' and mark it as completed."),
    ("remove", "Find and permanently delete the 'Water plants' reminder."),
]


async def main():
    instructions = load_instructions()

    async with MCPServerStreamableHttp(
        name="Tasks MCP Server",
        params={"url": "http://localhost:8000/mcp", "timeout": 10},
        cache_tools_list=True,
    ) as mcp_server:
        agent = Agent(
            name="Tasks Manager Agent",
            instructions=instructions,
            model=build_failover_model(),
            mcp_servers=[mcp_server],
        )

        results = []
        for test_name, prompt in TESTS:
            print(f"\n{'='*60}")
            print(f"TEST: {test_name}")
            print(f"PROMPT: {prompt}")
            print(f"{'='*60}")
            try:
                result = await Runner.run(agent, prompt)
                output = result.final_output.strip()
                print(f"RESULT: {output}")
                results.append((test_name, "PASS" if "error" not in output.lower() else "FAIL", output))
            except Exception as e:
                print(f"ERROR: {type(e).__name__}: {e}")
                results.append((test_name, "FAIL", str(e)))

        print(f"\n\n{'='*60}")
        print("SUMMARY REPORT")
        print(f"{'='*60}")
        all_pass = True
        for name, status, output in results:
            icon = "✅" if status == "PASS" else "❌"
            print(f"{icon} {name}: {status}")
            if status != "PASS":
                all_pass = False
        print(f"\nOverall: {'ALL PASSED' if all_pass else 'SOME FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())
