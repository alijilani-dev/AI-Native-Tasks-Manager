"""FailoverModel — wraps a primary and secondary model, falling back on failure."""

from typing import Any, AsyncIterator

from agents.agent_output import AgentOutputSchemaBase
from agents.handoffs import Handoff
from agents.items import ModelResponse, TResponseInputItem, TResponseStreamEvent
from agents.model_settings import ModelSettings
from agents.models.interface import Model, ModelTracing
from agents.tool import Tool


class FailoverModel(Model):
    """Wraps two Model instances. Calls primary first; on any exception, falls back to secondary."""

    def __init__(
        self, primary: Model, secondary: Model,
        primary_name: str = "primary", secondary_name: str = "secondary",
    ) -> None:
        self._primary = primary
        self._secondary = secondary
        self._primary_name = primary_name
        self._secondary_name = secondary_name
        self._fallback_used = False

    @property
    def fallback_used(self) -> bool:
        return self._fallback_used

    async def close(self) -> None:
        await self._primary.close()
        await self._secondary.close()

    def get_retry_advice(self, request: Any) -> Any:
        advice = self._primary.get_retry_advice(request)
        if advice is not None:
            return advice
        return self._secondary.get_retry_advice(request)

    async def get_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: Any | None,
    ) -> ModelResponse:
        try:
            return await self._primary.get_response(
                system_instructions=system_instructions,
                input=input,
                model_settings=model_settings,
                tools=tools,
                output_schema=output_schema,
                handoffs=handoffs,
                tracing=tracing,
                previous_response_id=previous_response_id,
                conversation_id=conversation_id,
                prompt=prompt,
            )
        except Exception:
            self._fallback_used = True
            return await self._secondary.get_response(
                system_instructions=system_instructions,
                input=input,
                model_settings=model_settings,
                tools=tools,
                output_schema=output_schema,
                handoffs=handoffs,
                tracing=tracing,
                previous_response_id=None,
                conversation_id=None,
                prompt=prompt,
            )

    def stream_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings,
        tools: list[Tool],
        output_schema: AgentOutputSchemaBase | None,
        handoffs: list[Handoff],
        tracing: ModelTracing,
        *,
        previous_response_id: str | None,
        conversation_id: str | None,
        prompt: Any | None,
    ) -> AsyncIterator[TResponseStreamEvent]:
        return self._StreamWrapper(
            self, system_instructions, input, model_settings, tools,
            output_schema, handoffs, tracing,
            previous_response_id=previous_response_id,
            conversation_id=conversation_id,
            prompt=prompt,
        )

    class _StreamWrapper:
        def __init__(self, model: "FailoverModel", *args: Any, **kwargs: Any) -> None:
            self._model = model
            self._args = args
            self._kwargs = kwargs

        def __aiter__(self) -> "FailoverModel._StreamWrapper":
            return self

        async def __anext__(self) -> TResponseStreamEvent:
            if not hasattr(self, "_stream"):
                try:
                    self._stream = self._model._primary.stream_response(
                        *self._args, **self._kwargs
                    ).__aiter__()
                    self._using_primary = True
                except Exception:
                    self._model._fallback_used = True
                    kwargs = dict(self._kwargs)
                    kwargs["previous_response_id"] = None
                    kwargs["conversation_id"] = None
                    self._stream = self._model._secondary.stream_response(
                        *self._args, **kwargs
                    ).__aiter__()
                    self._using_primary = False

            try:
                return await self._stream.__anext__()
            except StopAsyncIteration:
                raise
            except Exception:
                if self._using_primary:
                    self._model._fallback_used = True
                    kwargs = dict(self._kwargs)
                    kwargs["previous_response_id"] = None
                    kwargs["conversation_id"] = None
                    self._stream = self._model._secondary.stream_response(
                        *self._args, **kwargs
                    ).__aiter__()
                    self._using_primary = False
                    return await self._stream.__anext__()
                raise
