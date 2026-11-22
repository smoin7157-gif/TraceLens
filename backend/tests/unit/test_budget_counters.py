import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fakeredis.aioredis import FakeRedis

from tracelens.db.models.budget import Budget
from tracelens.security.budgets import BudgetCounterService


@pytest.mark.asyncio
async def test_budget_counter_accumulates_tokens() -> None:
    redis = FakeRedis()
    tenant_id = uuid.uuid4()
    key_id = uuid.uuid4()
    budget = Budget(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="test",
        daily_tokens=100,
        monthly_tokens=None,
        daily_usd=None,
        monthly_usd=None,
        webhook_url=None,
    )
    service = BudgetCounterService(redis)
    await service.record_usage(budget, tenant_id, key_id, tokens=15, cost_usd=Decimal("0"))
    await service.record_usage(budget, tenant_id, key_id, tokens=10, cost_usd=Decimal("0"))
    usage = await service.snapshot(tenant_id, key_id)
    assert usage.daily_tokens == 25
    assert service.exceeded_limit(budget, usage) is None


@pytest.mark.asyncio
async def test_budget_hard_stop_when_at_cap() -> None:
    redis = FakeRedis()
    tenant_id = uuid.uuid4()
    key_id = uuid.uuid4()
    budget = Budget(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="tight",
        daily_tokens=20,
        monthly_tokens=None,
        daily_usd=None,
        monthly_usd=None,
        webhook_url=None,
    )
    service = BudgetCounterService(redis)
    await service.record_usage(budget, tenant_id, key_id, tokens=20, cost_usd=Decimal("0"))
    usage = await service.snapshot(tenant_id, key_id)
    assert service.exceeded_limit(budget, usage) == "daily_tokens"


@pytest.mark.asyncio
async def test_budget_webhook_fires_once_per_window() -> None:
    redis = FakeRedis()
    tenant_id = uuid.uuid4()
    key_id = uuid.uuid4()
    budget = Budget(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="warn",
        daily_tokens=100,
        monthly_tokens=None,
        daily_usd=None,
        monthly_usd=None,
        webhook_url="https://example.test/hook",
    )
    service = BudgetCounterService(redis)
    with patch(
        "tracelens.security.budgets._post_webhook",
        new_callable=AsyncMock,
    ) as webhook_mock:
        await service.record_usage(budget, tenant_id, key_id, tokens=85, cost_usd=Decimal("0"))
        await service.record_usage(budget, tenant_id, key_id, tokens=1, cost_usd=Decimal("0"))
        await asyncio_pending_tasks()

    assert webhook_mock.call_count == 1


async def asyncio_pending_tasks() -> None:
    import asyncio

    await asyncio.sleep(0.05)
