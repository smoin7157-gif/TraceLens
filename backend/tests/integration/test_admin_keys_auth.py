import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.config.settings import get_settings
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_key_and_whoami(db_session, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_token = "test-admin-token"
    monkeypatch.setenv("ADMIN_API_TOKEN", admin_token)
    get_settings.cache_clear()

    tenant = await TenantRepository(db_session).create(
        name="Auth Test",
        slug=f"auth-{uuid.uuid4().hex[:8]}",
    )
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            f"/admin/tenants/{tenant.id}/api-keys",
            headers={"X-Admin-Token": admin_token},
            json={"name": "ci-key", "scopes": ["gateway"], "allowed_models": ["mock"]},
        )
        assert create_resp.status_code == 201
        secret = create_resp.json()["secret"]
        assert "secret" not in create_resp.json().get("key_hash", "")

        whoami = await client.get(
            "/v1/whoami",
            headers={"Authorization": f"Bearer {secret}"},
        )
        assert whoami.status_code == 200
        assert whoami.json()["tenant_id"] == str(tenant.id)

        list_resp = await client.get(
            f"/admin/tenants/{tenant.id}/api-keys",
            headers={"X-Admin-Token": admin_token},
        )
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 1
        assert "key_hash" not in list_resp.text

        key_id = items[0]["id"]
        revoke = await client.delete(
            f"/admin/tenants/{tenant.id}/api-keys/{key_id}",
            headers={"X-Admin-Token": admin_token},
        )
        assert revoke.status_code == 204

        denied = await client.get(
            "/v1/whoami",
            headers={"Authorization": f"Bearer {secret}"},
        )
        assert denied.status_code == 401
