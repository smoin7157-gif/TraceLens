import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.main import app


@pytest.mark.asyncio
async def test_models_list_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/models")
    assert response.status_code == 401
