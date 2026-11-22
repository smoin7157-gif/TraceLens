import uuid

import pytest
from fakeredis.aioredis import FakeRedis

from tracelens.optimize.cache import ExactCache, cache_prompt_digest
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


def _sample_response() -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id="chatcmpl-cache",
        created=1,
        model="mock-gpt",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="cached answer"),
            )
        ],
        usage=CompletionUsage(prompt_tokens=4, completion_tokens=2, total_tokens=6),
    )


@pytest.mark.asyncio
async def test_exact_cache_repeat_prompt_hits() -> None:
    redis = FakeRedis()
    tenant = uuid.uuid4()
    model = "mock-gpt"
    messages = [{"role": "user", "content": "same prompt"}]
    digest = cache_prompt_digest(messages, model)
    cache = ExactCache(redis)

    assert await cache.get(tenant, model, digest) is None
    await cache.set(tenant, model, digest, _sample_response())
    hit = await cache.get(tenant, model, digest)

    assert hit is not None
    assert hit.choices[0].message.content == "cached answer"
