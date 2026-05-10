import os

from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

from tasks_manager_agent.failover_model import FailoverModel

load_dotenv()

set_tracing_disabled(True)

# Primary stack (Gemini)
_PRIMARY_API_KEY = os.environ["TASKS_AGENT_PRIMARY_API_KEY"]
_PRIMARY_MODEL = os.environ["TASKS_AGENT_PRIMARY_MODEL"]

# Secondary stack (OpenAI)
_SECONDARY_API_KEY = os.environ["TASKS_AGENT_SECONDARY_API_KEY"]
_SECONDARY_MODEL = os.environ["TASKS_AGENT_SECONDARY_MODEL"]


def build_failover_model() -> FailoverModel:
    primary = OpenAIChatCompletionsModel(
        model=_PRIMARY_MODEL,
        openai_client=AsyncOpenAI(
            api_key=_PRIMARY_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        ),
    )
    secondary = OpenAIChatCompletionsModel(
        model=_SECONDARY_MODEL,
        openai_client=AsyncOpenAI(api_key=_SECONDARY_API_KEY),
    )
    return FailoverModel(
        primary=primary,
        secondary=secondary,
        primary_name=_PRIMARY_MODEL,
        secondary_name=_SECONDARY_MODEL,
    )
