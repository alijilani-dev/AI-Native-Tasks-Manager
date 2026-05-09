import os

from agents import Model as AgentModel
from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)

PROVIDER = os.environ.get("TASKS_AGENT_PROVIDER", "gemini").strip().lower()


def build_model() -> AgentModel:
    provider = PROVIDER

    if provider == "openai":
        return OpenAIChatCompletionsModel(
            model=os.environ["TASKS_AGENT_OPENAI_MODEL"],
            openai_client=AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"]),
        )

    return OpenAIChatCompletionsModel(
        model=os.environ["TASKS_AGENT_GEMINI_MODEL"],
        openai_client=AsyncOpenAI(
            api_key=os.environ["GEMINI_API_KEY"],
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        ),
    )
