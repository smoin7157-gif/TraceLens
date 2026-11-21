import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.tenant import Tenant


class TenantRepository:
    """Unscoped admin repository for tenant records (not tenant-owned data)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, name: str, slug: str) -> Tenant:
        tenant = Tenant(name=name, slug=slug)
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        result = await self.session.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self.session.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()
