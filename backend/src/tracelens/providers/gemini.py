import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from tracelens.config import get_settings
from tracelens.gateway.errors import ProviderError
from tracelens.providers.chunk_stream import stream_text_as_openai_chunks
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


class GeminiProvider:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._base_url = get_settings().google_base_url.rstrip("/")

    def _build_payload(self, request: ChatCompletionRequest) -> dict[str, Any]:
        contents = []
        for message in request.messages:
            role = "user" if message.role in {"user", "system"} else "model"
            contents.append({"role": role, "parts": [{"text": message.content}]})
        generation_config: dict[str, Any] = {}
        if request.temperature is not None:
            generation_config["temperature"] = request.temperature
        if request.max_tokens is not None:
            generation_config["maxOutputTokens"] = request.max_tokens
        return {"contents": contents, "generationConfig": generation_config}

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
            model_path = request.model
            url = f"{self._base_url}/models/{model_path}:generateContent"
            response = await client.post(
                url, params={"key": self._api_key}, json=self._build_payload(request)
            )
            if response.status_code >= 400:
                try:
                    msg = response.json().get("error", {}).get("message", response.text)
                except Exception:
                    msg = response.text
                if response.status_code == 429:
                    raise ProviderError(
                        msg,
                        status_code=429,
                        code="rate_limit_exceeded",
                        error_type="rate_limit_error",
                    )
                raise ProviderError(
                    msg,
                    status_code=response.status_code,
                    code="provider_error",
                    error_type="server_error",
                )

            data = response.json()
            candidates = data.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(part.get("text", "") for part in parts)
            usage_meta = data.get("usageMetadata") or {}
            prompt_tokens = int(usage_meta.get("promptTokenCount", 0))
            completion_tokens = int(usage_meta.get("candidatesTokenCount", 0))
            return ChatCompletionResponse(
                id=completion_id or "chatcmpl-gemini",
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=text),
                        finish_reason="stop",
                    )
                ],
                usage=CompletionUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
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
            {"id": "gemini-2.0-flash", "object": "model", "owned_by": "google"},
            {"id": "gemini-1.5-pro", "object": "model", "owned_by": "google"},
        ]
