import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from tracelens.config import get_settings
from tracelens.providers.chunk_stream import stream_text_as_openai_chunks
from tracelens.providers.errors import raise_from_http_response
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


class AnthropicProvider:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._base_url = get_settings().anthropic_base_url.rstrip("/")

    def _build_payload(self, request: ChatCompletionRequest) -> dict[str, Any]:
        system_parts = [m.content for m in request.messages if m.role == "system"]
        messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
            if m.role in {"user", "assistant"}
        ]
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
        }
        if system_parts:
            payload["system"] = "\n".join(system_parts)
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        return payload

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        completion_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> ChatCompletionResponse:
        owns_client = client is None
        client = client or httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
        try:
            response = await client.post(
                f"{self._base_url}/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=self._build_payload(request),
            )
            if response.status_code >= 400:
                raise_from_http_response(response)
            data = response.json()
            text_parts = [
                block["text"] for block in data.get("content", []) if block.get("type") == "text"
            ]
            content = "".join(text_parts)
            usage = data.get("usage") or {}
            return ChatCompletionResponse(
                id=completion_id or data.get("id", "chatcmpl-anthropic"),
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=content),
                        finish_reason="stop",
                    )
                ],
                usage=CompletionUsage(
                    prompt_tokens=int(usage.get("input_tokens", 0)),
                    completion_tokens=int(usage.get("output_tokens", 0)),
                    total_tokens=int(usage.get("input_tokens", 0))
                    + int(usage.get("output_tokens", 0)),
                ),
            )
        finally:
            if owns_client:
                await client.aclose()

    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        *,
        completion_id: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        response = await self.chat_completion(
            request,
            completion_id=completion_id,
            client=client,
        )
        stream_id = completion_id or response.id
        async for chunk in stream_text_as_openai_chunks(
            request,
            completion_id=stream_id,
            full_text=response.choices[0].message.content,
        ):
            yield chunk

    def static_models(self) -> list[dict[str, str]]:
        return [
            {"id": "claude-3-5-sonnet-latest", "object": "model", "owned_by": "anthropic"},
            {"id": "claude-3-5-haiku-latest", "object": "model", "owned_by": "anthropic"},
        ]
