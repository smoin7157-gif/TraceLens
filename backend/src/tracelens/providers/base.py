from collections.abc import AsyncIterator
from typing import Any, Protocol

from tracelens.providers.schemas import ChatCompletionRequest, ChatCompletionResponse


class ChatProvider(Protocol):
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse: ...

    def chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        *,
        completion_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]: ...
