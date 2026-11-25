import uuid
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.request_log import RequestLog


async def tenant_economics_summary(
    session: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict[str, object]:
    savings_expr = RequestLog.cost_without_optimization - RequestLog.cost_actual
    cache_hit_expr = case(
        (RequestLog.cache_status.in_(("exact", "semantic")), 1),
        else_=0,
    )
    stmt = select(
        func.count(RequestLog.id),
        func.coalesce(func.sum(savings_expr), 0),
        func.coalesce(func.sum(cache_hit_expr), 0),
    ).where(RequestLog.tenant_id == tenant_id)
    count, savings_sum, cache_hits = (await session.execute(stmt)).one()
    count_i = int(count or 0)
    return {
        "request_count": count_i,
        "total_savings_usd": str(savings_sum or Decimal("0")),
        "cache_hit_rate": (int(cache_hits or 0) / count_i) if count_i else 0.0,
    }


async def tenant_security_summary(
    session: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict[str, object]:
    blocked_expr = case((RequestLog.status != "completed", 1), else_=0)
    stmt = select(
        func.count(RequestLog.id),
        func.coalesce(func.sum(blocked_expr), 0),
    ).where(RequestLog.tenant_id == tenant_id)
    total, blocked = (await session.execute(stmt)).one()
    total_i = int(total or 0)
    return {
        "tenant_id": str(tenant_id),
        "blocked_or_error_requests": int(blocked or 0),
        "total_reviewed": total_i,
    }
