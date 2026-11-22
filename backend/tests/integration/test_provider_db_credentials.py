import uuid

import pytest
from cryptography.fernet import Fernet

from tracelens.db.models.provider import Provider
from tracelens.providers.credentials import resolve_api_key
from tracelens.security.credentials import CredentialCipher


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resolve_api_key_from_encrypted_db_row(
    db_session, monkeypatch: pytest.MonkeyPatch
) -> None:
    master_key = Fernet.generate_key().decode()
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", master_key)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from tracelens.config.settings import get_settings

    get_settings.cache_clear()

    cipher = CredentialCipher(master_key)
    token = cipher.encrypt_json({"api_key": "sk-from-db"})
    db_session.add(
        Provider(
            provider_type="openai",
            name=f"openai-{uuid.uuid4().hex[:6]}",
            encrypted_credentials=token,
            enabled=True,
        )
    )
    await db_session.commit()

    key = await resolve_api_key(db_session, "openai")
    assert key == "sk-from-db"
