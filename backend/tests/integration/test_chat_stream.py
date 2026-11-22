import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.config.settings import get_settings
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mock_chat_stream_sse(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_token = "test-admin-token"
    monkeypatch.setenv("ADMIN_API_TOKEN", admin_token)
    get_settings.cache_clear()

    tenant = await TenantRepository(db_session).create(
        name="Stream Test",
        slug=f"stream-{uuid.uuid4().hex[:8]}",
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        secret = (
            await client.post(
                f"/admin/tenants/{tenant.id}/api-keys",
                headers={"X-Admin-Token": admin_token},
                json={"name": "stream", "scopes": ["gateway"], "allowed_models": ["mock-gpt"]},
            )
        ).json()["secret"]

        async with client.stream(
            "POST",
            "/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {secret}",
                "X-TraceLens-Mock-Latency-Ms": "0",
            },
            json={
                "model": "mock-gpt",
                "stream": True,
                "messages": [{"role": "user", "content": "stream me"}],
            },
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            events: list[str] = []
            async for line in response.aiter_lines():
                if line:
                    events.append(line)

    assert any(line == "data: [DONE]" for line in events)
    data_lines = [line for line in events if line.startswith("data: ") and line != "data: [DONE]"]
    assert data_lines
    assert any("chat.completion.chunk" in line for line in data_lines)
