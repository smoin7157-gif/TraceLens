import time
from typing import Any, Literal

import httpx

from tracelens.config import get_settings
from tracelens.providers.errors import raise_from_http_response
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


def _coerce_finish_reason(value: str | None) -> Literal["stop", "length"]:
    if value == "length":
        return "length"
    return "stop"


def _map_completion(
    data: dict[str, Any], fallback_model: str, fallback_id: str | None
) -> ChatCompletionResponse:
    choice0 = data["choices"][0]
    usage = data.get("usage") or {}
    return ChatCompletionResponse(
        id=fallback_id or data.get("id") or "chatcmpl-unknown",
        created=data.get("created") or int(time.time()),
        model=data.get("model") or fallback_model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=choice0["message"]["content"],
                ),
                finish_reason=_coerce_finish_reason(choice0.get("finish_reason")),
            )
        ],
        usage=CompletionUsage(
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            total_tokens=int(usage.get("total_tokens", 0)),
        ),
    )


class OpenAIProvider:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._base_url = get_settings().openai_base_url.rstrip("/")

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
            payload: dict[str, Any] = {
                "model": request.model,
                "messages": [m.model_dump() for m in request.messages],
                "stream": False,
            }
            if request.temperature is not None:
                payload["temperature"] = request.temperature
            if request.max_tokens is not None:
                payload["max_tokens"] = request.max_tokens

            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
            )
            if response.status_code >= 400:
                raise_from_http_response(response)
            return _map_completion(response.json(), request.model, completion_id)
        finally:
            if owns_client:
                await client.aclose()

    async def list_models(self, client: httpx.AsyncClient | None = None) -> list[dict[str, str]]:
        owns_client = client is None
        client = client or httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
        try:
            response = await client.get(
                f"{self._base_url}/models",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            if response.status_code >= 400:
                raise_from_http_response(response)
            data = response.json().get("data", [])
            return [
                {"id": item["id"], "object": "model", "owned_by": item.get("owned_by", "openai")}
                for item in data
            ]
        finally:
            if owns_client:
                await client.aclose()
