import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.api_key import ApiKey
from tracelens.db.repositories.base import TenantScopedRepository


class ApiKeyRepository(TenantScopedRepository[ApiKey]):
    model = ApiKey

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id)

    async def create(
        self,
        *,
        key_hash: str,
        key_prefix: str,
        name: str,
        scopes: list[str],
        allowed_models: list[str],
    ) -> ApiKey:
        entity = ApiKey(
            tenant_id=self.tenant_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            scopes=scopes,
            allowed_models=allowed_models,
        )
        return await self.add(entity)

    async def list_keys(self) -> list[ApiKey]:
        return await self.list_all(limit=500)

    async def revoke(self, key_id: uuid.UUID) -> ApiKey | None:
        key = await self.get_by_id(key_id)
        if key is None:
            return None
        key.revoked_at = datetime.now(UTC)
        await self.session.flush()
        return key


class ApiKeyAuthRepository:
    """Global lookup for bearer authentication (verify before trusting)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_active_by_prefix(self, key_prefix: str) -> list[ApiKey]:
        stmt = select(ApiKey).where(
            ApiKey.key_prefix == key_prefix,
            ApiKey.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
