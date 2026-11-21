import asyncio
import random
import time
import uuid

from fastapi import Request

from tracelens.config import get_settings
from tracelens.gateway.errors import ProviderError
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


def _parse_mock_headers(request: Request | None) -> tuple[float, float, int | None]:
    settings = get_settings()
    latency_ms = settings.mock_default_latency_ms
    error_rate = settings.mock_default_error_rate
    seed: int | None = None

    if request is not None:
        if h := request.headers.get("X-TraceLens-Mock-Latency-Ms"):
            latency_ms = float(h)
        if h := request.headers.get("X-TraceLens-Mock-Error-Rate"):
            error_rate = float(h)
        if h := request.headers.get("X-TraceLens-Mock-Seed"):
            seed = int(h)

    return latency_ms, error_rate, seed


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


class MockProvider:
    """Controllable provider for tests, chaos, and benchmarks."""

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        http_request: Request | None = None,
        completion_id: str | None = None,
    ) -> ChatCompletionResponse:
        latency_ms, error_rate, seed = _parse_mock_headers(http_request)
        rng = random.Random(seed)

        if latency_ms > 0:
            await asyncio.sleep(latency_ms / 1000.0)

        if rng.random() < error_rate:
            if rng.random() < 0.5:
                raise ProviderError(
                    "Mock rate limit triggered",
                    status_code=429,
                    code="rate_limit_exceeded",
                    error_type="rate_limit_error",
                )
            raise ProviderError(
                "Mock internal error",
                status_code=500,
                code="server_error",
                error_type="server_error",
            )

        user_messages = [m.content for m in request.messages if m.role == "user"]
        last_user = user_messages[-1] if user_messages else ""
        reply = f"[mock:{request.model}] {last_user}"

        prompt_tokens = sum(_estimate_tokens(m.content) for m in request.messages)
        completion_tokens = _estimate_tokens(reply)

        return ChatCompletionResponse(
            id=completion_id or f"chatcmpl-{uuid.uuid4().hex[:12]}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=reply),
                    finish_reason="stop",
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )
