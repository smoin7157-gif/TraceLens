from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.gateway.errors import GatewayValidationError
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.mock import MockProvider


class ProviderStage:
    name = "provider"

    def __init__(self, _session: AsyncSession) -> None:
        self._mock = MockProvider()

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.chat_request is None:
            raise GatewayValidationError("Chat request missing on gateway context")

        model = context.chat_request.model
        if not model.startswith("mock-"):
            raise GatewayValidationError(
                f"The model `{model}` does not exist or you do not have access to it.",
                code="model_not_found",
            )

        context.chat_response = await self._mock.chat_completion(
            context.chat_request,
            http_request=request,
            completion_id=context.request_id,
        )
