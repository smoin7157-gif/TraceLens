import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.request_log import RequestLog


async def weekly_savings_report(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    days: int = 7,
) -> dict[str, object]:
    since = datetime.now(UTC) - timedelta(days=days)
    stmt = select(
        func.count(RequestLog.id),
        func.coalesce(func.sum(RequestLog.cost_actual), 0),
        func.coalesce(func.sum(RequestLog.cost_without_optimization), 0),
    ).where(
        RequestLog.tenant_id == tenant_id,
        RequestLog.created_at >= since,
        RequestLog.status == "completed",
    )
    row = (await session.execute(stmt)).one()
    count, cost_actual, cost_without = row
    savings = Decimal(str(cost_without)) - Decimal(str(cost_actual))
    return {
        "tenant_id": str(tenant_id),
        "period_days": days,
        "since": since.isoformat(),
        "request_count": int(count),
        "cost_actual_usd": str(cost_actual),
        "cost_without_optimization_usd": str(cost_without),
        "savings_usd": str(savings),
    }
