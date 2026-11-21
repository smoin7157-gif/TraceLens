import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.main import app


@pytest.mark.asyncio
async def test_whoami_missing_bearer_returns_openai_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/whoami")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["type"] == "invalid_request_error"
    assert body["error"]["code"] == "missing_api_key"


@pytest.mark.asyncio
async def test_whoami_invalid_format_returns_invalid_api_key() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/v1/whoami",
            headers={"Authorization": "Bearer not-a-tracelens-key"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_api_key"
