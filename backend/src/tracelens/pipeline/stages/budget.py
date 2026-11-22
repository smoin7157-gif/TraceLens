from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.redis_client import RedisClient
from tracelens.gateway.errors import GatewayBudgetError
from tracelens.observe.request_log import load_budget_for_context
from tracelens.pipeline.context import GatewayContext
from tracelens.security.budgets import BudgetCounterService


class BudgetStage:
    name = "budget"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run(self, _request: Request, context: GatewayContext) -> None:
        if context.tenant_id is None or context.key_id is None or context.budget_id is None:
            return

        budget = await load_budget_for_context(self._session, context)
        if budget is None:
            return

        counters = BudgetCounterService(RedisClient.connection())
        context.budget_snapshot = await counters.snapshot(context.tenant_id, context.key_id)
        exceeded = counters.exceeded_limit(budget, context.budget_snapshot)
        if exceeded is not None:
            raise GatewayBudgetError(
                f"Budget exceeded for {exceeded}",
                code="insufficient_quota",
                limit=exceeded,
            )
