import time
from unittest.mock import patch

import pytest
from fakeredis.aioredis import FakeRedis

from tracelens.resilience.circuit_breaker import CircuitBreaker, CircuitState, circuit_scope_key


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures() -> None:
    redis = FakeRedis()
    scope = circuit_scope_key("tenant-1", "mock", "mock-gpt")
    breaker = CircuitBreaker(redis, scope)

    assert await breaker.allow_request() is True
    assert await breaker.get_state() == CircuitState.CLOSED

    for _ in range(5):
        await breaker.record_failure()

    assert await breaker.get_state() == CircuitState.OPEN
    assert await breaker.allow_request() is False


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_then_closes_on_success() -> None:
    redis = FakeRedis()
    scope = circuit_scope_key("tenant-1", "mock", "mock-gpt")
    breaker = CircuitBreaker(redis, scope)

    for _ in range(5):
        await breaker.record_failure()

    future = time.time() + 31.0
    with patch("tracelens.resilience.circuit_breaker.time.time", return_value=future):
        assert await breaker.allow_request() is True
        assert await breaker.get_state() == CircuitState.HALF_OPEN

    await breaker.record_success()
    assert await breaker.get_state() == CircuitState.CLOSED
    assert await breaker.allow_request() is True
