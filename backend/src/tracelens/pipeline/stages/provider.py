from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.gateway.errors import GatewayValidationError
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.registry import ProviderRegistry


class ProviderStage:
    name = "provider"

    def __init__(self, session: AsyncSession) -> None:
        self._registry = ProviderRegistry(session)

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.chat_request is None:
            raise GatewayValidationError("Chat request missing on gateway context")

        context.chat_response = await self._registry.chat_completion(
            context.chat_request,
            http_request=request,
            completion_id=context.request_id,
        )
