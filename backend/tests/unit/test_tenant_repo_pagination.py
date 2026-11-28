import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.tenant import Tenant
from tracelens.db.repositories.tenant import TenantRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tenant_list_offset(db_session: AsyncSession) -> None:
    for idx in range(3):
        db_session.add(Tenant(id=uuid.uuid4(), name=f"T{idx}", slug=f"pag-{idx}"))
    await db_session.flush()
    repo = TenantRepository(db_session)
    page0 = await repo.list_recent(limit=1, offset=0)
    page1 = await repo.list_recent(limit=1, offset=1)
    assert len(page0) == 1
    assert len(page1) == 1
    assert page0[0].id != page1[0].id