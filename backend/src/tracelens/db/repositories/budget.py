import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.budget import Budget
from tracelens.db.repositories.base import TenantScopedRepository


class BudgetRepository(TenantScopedRepository[Budget]):
    model = Budget

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id)

    async def create(
        self,
        *,
        name: str,
        daily_tokens: int | None = None,
        monthly_tokens: int | None = None,
        daily_usd: Decimal | None = None,
        monthly_usd: Decimal | None = None,
        webhook_url: str | None = None,
    ) -> Budget:
        entity = Budget(
            tenant_id=self.tenant_id,
            name=name,
            daily_tokens=daily_tokens,
            monthly_tokens=monthly_tokens,
            daily_usd=daily_usd,
            monthly_usd=monthly_usd,
            webhook_url=webhook_url,
        )
        return await self.add(entity)
