import time
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fakeredis.aioredis import FakeRedis

from tracelens.db.redis_client import RedisClient
from tracelens.observe.trace_queue import enqueue_trace
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


@pytest.mark.asyncio
async def test_trace_enqueue_fail_open_on_redis_error() -> None:
    request = MagicMock()
    request.method = "POST"
    context = GatewayContext(
        tenant_id=uuid.uuid4(),
        trace_id=uuid.uuid4().hex,
        root_span_id=uuid.uuid4().hex[:16],
        chat_request=ChatCompletionRequest(
            model="mock-gpt",
            messages=[ChatMessage(role="user", content="hi")],
        ),
        stages_executed=["auth", "provider"],
    )

    with patch.object(RedisClient, "connection", side_effect=RuntimeError("redis down")):
        await enqueue_trace(request, context)


@pytest.mark.asyncio
async def test_trace_enqueue_p95_under_2ms_simulation() -> None:
    fake = FakeRedis()
    request = MagicMock()
    request.method = "POST"
    durations_ms: list[float] = []

    with patch.object(RedisClient, "connection", return_value=fake):
        for _ in range(100):
            context = GatewayContext(
                tenant_id=uuid.uuid4(),
                trace_id=uuid.uuid4().hex,
                root_span_id=uuid.uuid4().hex[:16],
                chat_request=ChatCompletionRequest(
                    model="mock-gpt",
                    messages=[ChatMessage(role="user", content="load test")],
                ),
                stages_executed=["auth", "provider"],
            )
            started = time.perf_counter()
            await enqueue_trace(request, context)
            durations_ms.append((time.perf_counter() - started) * 1000.0)

    durations_ms.sort()
    p95_index = int(len(durations_ms) * 0.95) - 1
    assert durations_ms[p95_index] < 2.0
