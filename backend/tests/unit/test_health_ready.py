import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.main import app


@pytest.mark.asyncio
async def test_health_ready_shape() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "checks" in body
    assert "postgres" in body["checks"]
    assert "redis" in body["checks"]
