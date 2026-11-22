from unittest.mock import patch

import pytest
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient

from tracelens.main import app


@pytest.mark.asyncio
async def test_provider_health_endpoint() -> None:
    fake = FakeRedis()
    with patch("tracelens.gateway.health.RedisClient.connection", return_value=fake):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/providers")

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "provider_health"
    assert isinstance(body["data"], list)
    assert any(item["model"] == "mock-gpt" for item in body["data"])
