import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import httpx
from redis.asyncio import Redis

from tracelens.config import get_settings
from tracelens.db.models.budget import Budget


@dataclass(frozen=True)
class UsageSnapshot:
    daily_tokens: int
    monthly_tokens: int
    daily_usd: float
    monthly_usd: float


def _day_bucket() -> str:
    return datetime.now(UTC).strftime("%Y%m%d")


def _month_bucket() -> str:
    return datetime.now(UTC).strftime("%Y%m")


def counter_key(
    tenant_id: uuid.UUID,
    key_id: uuid.UUID,
    metric: str,
    period_bucket: str,
) -> str:
    return f"tl:budget:{tenant_id}:{key_id}:{metric}:{period_bucket}"


def warn_sent_key(tenant_id: uuid.UUID, key_id: uuid.UUID, metric: str, period: str) -> str:
    return f"tl:budget:warn:{tenant_id}:{key_id}:{metric}:{period}"


class BudgetCounterService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def snapshot(self, tenant_id: uuid.UUID, key_id: uuid.UUID) -> UsageSnapshot:
        day = _day_bucket()
        month = _month_bucket()
        daily_tokens = int(
            await self._redis.get(counter_key(tenant_id, key_id, "daily_tokens", day)) or 0
        )
        monthly_tokens = int(
            await self._redis.get(counter_key(tenant_id, key_id, "monthly_tokens", month)) or 0
        )
        daily_usd = float(
            await self._redis.get(counter_key(tenant_id, key_id, "daily_usd", day)) or 0.0
        )
        monthly_usd = float(
            await self._redis.get(counter_key(tenant_id, key_id, "monthly_usd", month)) or 0.0
        )
        return UsageSnapshot(daily_tokens, monthly_tokens, daily_usd, monthly_usd)

    def exceeded_limit(self, budget: Budget, usage: UsageSnapshot) -> str | None:
        if budget.daily_tokens is not None and usage.daily_tokens >= budget.daily_tokens:
            return "daily_tokens"
        if budget.monthly_tokens is not None and usage.monthly_tokens >= budget.monthly_tokens:
            return "monthly_tokens"
        if budget.daily_usd is not None and usage.daily_usd >= float(budget.daily_usd):
            return "daily_usd"
        if budget.monthly_usd is not None and usage.monthly_usd >= float(budget.monthly_usd):
            return "monthly_usd"
        return None

    async def record_usage(
        self,
        budget: Budget,
        tenant_id: uuid.UUID,
        key_id: uuid.UUID,
        *,
        tokens: int,
        cost_usd: Decimal,
    ) -> UsageSnapshot:
        day = _day_bucket()
        month = _month_bucket()
        pipe = self._redis.pipeline(transaction=True)
        pipe.incrby(counter_key(tenant_id, key_id, "daily_tokens", day), tokens)
        pipe.expire(counter_key(tenant_id, key_id, "daily_tokens", day), 60 * 60 * 48)
        pipe.incrby(counter_key(tenant_id, key_id, "monthly_tokens", month), tokens)
        pipe.expire(counter_key(tenant_id, key_id, "monthly_tokens", month), 60 * 60 * 24 * 45)
        cost_float = float(cost_usd)
        if cost_float > 0:
            pipe.incrbyfloat(counter_key(tenant_id, key_id, "daily_usd", day), cost_float)
            pipe.expire(counter_key(tenant_id, key_id, "daily_usd", day), 60 * 60 * 48)
            pipe.incrbyfloat(counter_key(tenant_id, key_id, "monthly_usd", month), cost_float)
            pipe.expire(counter_key(tenant_id, key_id, "monthly_usd", month), 60 * 60 * 24 * 45)
        await pipe.execute()
        usage = await self.snapshot(tenant_id, key_id)
        if budget.webhook_url:
            await self._maybe_send_warnings(budget, tenant_id, key_id, usage)
        return usage

    async def _maybe_send_warnings(
        self,
        budget: Budget,
        tenant_id: uuid.UUID,
        key_id: uuid.UUID,
        usage: UsageSnapshot,
    ) -> None:
        settings = get_settings().budget
        checks: list[tuple[str, str, float, float | None]] = [
            ("daily_tokens", _day_bucket(), float(usage.daily_tokens), budget.daily_tokens),
            ("monthly_tokens", _month_bucket(), float(usage.monthly_tokens), budget.monthly_tokens),
            (
                "daily_usd",
                _day_bucket(),
                usage.daily_usd,
                float(budget.daily_usd) if budget.daily_usd else None,
            ),
            (
                "monthly_usd",
                _month_bucket(),
                usage.monthly_usd,
                float(budget.monthly_usd) if budget.monthly_usd else None,
            ),
        ]
        for metric, period, current, cap in checks:
            if cap is None or cap <= 0:
                continue
            if current / cap < settings.warn_fraction:
                continue
            sent_key = warn_sent_key(tenant_id, key_id, metric, period)
            claimed = await self._redis.set(
                sent_key,
                "1",
                nx=True,
                ex=settings.warn_dedupe_seconds,
            )
            if not claimed:
                continue
            payload = {
                "event": "budget_threshold",
                "tenant_id": str(tenant_id),
                "api_key_id": str(key_id),
                "metric": metric,
                "current": current,
                "limit": cap,
                "fraction": round(current / cap, 4),
            }
            url = budget.webhook_url
            if url:
                asyncio.create_task(_post_webhook(url, payload))


async def _post_webhook(url: str, payload: dict[str, object]) -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json=payload)
    except Exception:
        return None


async def reconcile_counters_to_postgres() -> None:
    """Placeholder for periodic PG reconcile (phase 9 skeleton)."""
    return None
