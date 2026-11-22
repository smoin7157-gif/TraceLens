from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.config import get_settings
from tracelens.db.models.provider import Provider
from tracelens.security.credentials import get_cipher

ProviderKind = str  # openai | anthropic | gemini


async def resolve_api_key(session: AsyncSession | None, provider: ProviderKind) -> str | None:
    """Resolve API key from environment (dev) or encrypted DB row."""
    settings = get_settings()
    env_map = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "gemini": settings.google_api_key,
    }
    env_value = env_map.get(provider, "")
    if env_value:
        return env_value

    if session is None:
        return None

    stmt = select(Provider).where(Provider.provider_type == provider, Provider.enabled.is_(True))
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        return None

    cipher = get_cipher()
    if cipher is None:
        return None
    secrets = cipher.decrypt_json(row.encrypted_credentials)
    api_key = secrets.get("api_key")
    return str(api_key) if api_key else None
