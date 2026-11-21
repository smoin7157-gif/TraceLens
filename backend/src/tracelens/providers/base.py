from typing import Protocol

from tracelens.providers.schemas import ChatCompletionRequest, ChatCompletionResponse


class ChatProvider(Protocol):
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse: ...
