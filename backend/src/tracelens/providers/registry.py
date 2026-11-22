from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.gateway.errors import GatewayValidationError
from tracelens.providers.anthropic import AnthropicProvider
from tracelens.providers.credentials import resolve_api_key
from tracelens.providers.gemini import GeminiProvider
from tracelens.providers.mock import MockProvider
from tracelens.providers.openai import OpenAIProvider
from tracelens.providers.router import ProviderKind, resolve_provider_for_model
from tracelens.providers.schemas import ChatCompletionRequest, ChatCompletionResponse


class ProviderRegistry:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._mock = MockProvider()

    def kind_for_model(self, model: str) -> ProviderKind:
        return resolve_provider_for_model(model)

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        http_request: Request | None,
        completion_id: str | None,
    ) -> ChatCompletionResponse:
        kind = self.kind_for_model(request.model)
        if kind == "mock":
            return await self._mock.chat_completion(
                request,
                http_request=http_request,
                completion_id=completion_id,
            )

        api_key = await resolve_api_key(self._session, kind)
        if not api_key:
            raise GatewayValidationError(
                f"Provider `{kind}` is not configured for this installation.",
                code="provider_not_configured",
            )

        if kind == "openai":
            return await OpenAIProvider(api_key).chat_completion(
                request, completion_id=completion_id
            )
        if kind == "anthropic":
            return await AnthropicProvider(api_key).chat_completion(
                request, completion_id=completion_id
            )
        if kind == "gemini":
            return await GeminiProvider(api_key).chat_completion(
                request, completion_id=completion_id
            )

        raise GatewayValidationError(
            f"The model `{request.model}` does not exist or you do not have access to it.",
            code="model_not_found",
        )
