import json
from typing import Any, cast

from cryptography.fernet import Fernet, InvalidToken

from tracelens.config import get_settings


class CredentialCipher:
    """Fernet encryption for provider secrets at rest (MASTER_ENCRYPTION_KEY)."""

    def __init__(self, master_key: str) -> None:
        if not master_key:
            raise ValueError("MASTER_ENCRYPTION_KEY is required to encrypt provider credentials")
        self._fernet = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)

    def encrypt_json(self, payload: dict[str, Any]) -> str:
        token = self._fernet.encrypt(json.dumps(payload).encode("utf-8"))
        return token.decode("utf-8")

    def decrypt_json(self, token: str) -> dict[str, Any]:
        try:
            data = self._fernet.decrypt(token.encode("utf-8"))
        except InvalidToken as exc:
            raise ValueError("Invalid encrypted credential blob") from exc
        return cast(dict[str, Any], json.loads(data.decode("utf-8")))


def get_cipher() -> CredentialCipher | None:
    key = get_settings().master_encryption_key
    if not key:
        return None
    return CredentialCipher(key)
