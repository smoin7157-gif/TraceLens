import uuid

import pytest

from tracelens.optimize.semantic import SemanticCache
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_cache_isolated_by_tenant(db_session) -> None:
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    model = "mock-gpt"
    messages = [{"role": "user", "content": "shared prompt for semantic cache"}]
    response = ChatCompletionResponse(
        id="cached",
        created=1,
        model=model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="tenant-a-only"),
            )
        ],
        usage=CompletionUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
    )

    cache = SemanticCache(db_session)
    await cache.store(tenant_a, model, messages, "hash-a", response)
    await db_session.commit()

    hit_a, score_a = await cache.lookup(tenant_a, model, messages)
    hit_b, _score_b = await cache.lookup(tenant_b, model, messages)

    assert hit_a is not None
    assert score_a is not None and score_a >= 0.92
    assert hit_b is None
