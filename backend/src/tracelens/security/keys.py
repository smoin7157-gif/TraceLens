import re
import secrets
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_API_KEY_PATTERN = re.compile(r"^tl_([a-zA-Z0-9]{8})_([A-Za-z0-9_-]{16,})$")
_hasher = PasswordHasher()


@dataclass(frozen=True)
class ApiKeyMaterial:
    """Plaintext key returned once at creation; only hash is stored."""

    raw_key: str
    key_prefix: str
    key_hash: str


def issue_api_key() -> ApiKeyMaterial:
    prefix_body = secrets.token_hex(4)
    secret = secrets.token_urlsafe(24)
    key_prefix = f"tl_{prefix_body}"
    raw_key = f"{key_prefix}_{secret}"
    key_hash = hash_api_key(raw_key)
    return ApiKeyMaterial(raw_key=raw_key, key_prefix=key_prefix, key_hash=key_hash)


def hash_api_key(raw_key: str) -> str:
    return _hasher.hash(raw_key)


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    try:
        return _hasher.verify(key_hash, raw_key)
    except VerifyMismatchError:
        return False


def parse_api_key(raw_key: str) -> tuple[str, str] | None:
    """Return (key_prefix, raw_key) when format is valid."""
    match = _API_KEY_PATTERN.match(raw_key.strip())
    if match is None:
        return None
    key_prefix = f"tl_{match.group(1)}"
    return key_prefix, raw_key.strip()


def mask_api_key(raw_key: str) -> str:
    parsed = parse_api_key(raw_key)
    if parsed is None:
        return "****"
    prefix, _ = parsed
    return f"{prefix}_****"
