import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.dataset import Dataset, DatasetItem
from tracelens.db.models.request_log import RequestLog


async def create_dataset(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str,
    description: str = "",
) -> Dataset:
    entity = Dataset(tenant_id=tenant_id, name=name, description=description)
    session.add(entity)
    await session.flush()
    return entity


async def import_from_request_logs(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    dataset_id: uuid.UUID,
    request_log_ids: list[uuid.UUID],
) -> int:
    stmt = select(RequestLog).where(
        RequestLog.tenant_id == tenant_id,
        RequestLog.id.in_(request_log_ids),
    )
    logs = list((await session.execute(stmt)).scalars().all())
    added = 0
    for row in logs:
        item = DatasetItem(
            tenant_id=tenant_id,
            dataset_id=dataset_id,
            request_log_id=row.id,
            input={
                "model": row.model,
                "selected_model": row.selected_model,
                "routing_explanation": row.routing_explanation,
            },
            expected_output=None,
        )
        session.add(item)
        added += 1
    await session.flush()
    return added
