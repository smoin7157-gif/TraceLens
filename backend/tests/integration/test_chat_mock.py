import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.config.settings import get_settings
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_completions_mock_end_to_end(
    db_session, monkeypatch: pytest.MonkeyPatch
) -> None:
    admin_token = "test-admin-token"
    monkeypatch.setenv("ADMIN_API_TOKEN", admin_token)
    get_settings.cache_clear()

    tenant = await TenantRepository(db_session).create(
        name="Chat Test",
        slug=f"chat-{uuid.uuid4().hex[:8]}",
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            f"/admin/tenants/{tenant.id}/api-keys",
            headers={"X-Admin-Token": admin_token},
            json={"name": "gateway", "scopes": ["gateway"], "allowed_models": ["mock-gpt"]},
        )
        secret = create_resp.json()["secret"]

        chat_resp = await client.post(
            "/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {secret}",
                "X-TraceLens-Mock-Latency-Ms": "0",
                "X-TraceLens-Mock-Error-Rate": "0",
            },
            json={
                "model": "mock-gpt",
                "messages": [{"role": "user", "content": "Hello TraceLens"}],
                "stream": False,
            },
        )
        assert chat_resp.status_code == 200
        payload = chat_resp.json()
        assert payload["object"] == "chat.completion"
        assert payload["tracelens"]["tenant_id"] == str(tenant.id)
        assert payload["tracelens"]["stages"] == [
            "auth",
            "rate_limit",
            "validation",
            "security_scan",
            "budget",
            "router",
            "provider",
            "request_log",
            "trace_enqueue",
        ]
        assert "Hello TraceLens" in payload["choices"][0]["message"]["content"]
