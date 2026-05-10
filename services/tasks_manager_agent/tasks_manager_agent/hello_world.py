"""Phase 1: Hello world — verify failover model works."""

import asyncio

from agents import Agent, Runner

from tasks_manager_agent.config import build_failover_model


async def main():
    agent = Agent(
        name="HelloAgent",
        instructions="You are a helpful assistant. Respond concisely.",
        model=build_failover_model(),
    )

    result = await Runner.run(agent, "Say hello world and tell me what model you are.")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
