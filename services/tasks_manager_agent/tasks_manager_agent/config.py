import os

from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)


def build_gemini_model() -> OpenAIChatCompletionsModel:
    """Build a Gemini-compatible model via OpenAI Chat Completions adapter."""
    client = AsyncOpenAI(
        api_key=os.environ["GEMINI_API_KEY"],
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    return OpenAIChatCompletionsModel(
        model="gemini-2.5-flash-lite-preview",
        openai_client=client,
    )
