from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.gateway.errors import GatewayValidationError
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.registry import ProviderRegistry
from tracelens.providers.retry import call_provider_with_retry_placeholder, retry_metadata


class ProviderStage:
    name = "provider"

    def __init__(self, session: AsyncSession) -> None:
        self._registry = ProviderRegistry(session)

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.chat_request is None:
            raise GatewayValidationError("Chat request missing on gateway context")

        context.metadata.update(retry_metadata())

        if context.chat_request.stream:
            await self._registry.ensure_provider_ready(context.chat_request.model)
            context.stream_chunks = self._registry.chat_completion_stream(
                context.chat_request,
                http_request=request,
                completion_id=context.request_id,
            )
            return

        context.chat_response = await call_provider_with_retry_placeholder(
            self._registry.chat_completion,
            context.chat_request,
            http_request=request,
            completion_id=context.request_id,
        )
