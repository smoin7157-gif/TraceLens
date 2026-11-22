from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.budget import Budget
from tracelens.db.redis_client import RedisClient
from tracelens.db.repositories.request_log import RequestLogRepository
from tracelens.pipeline.context import GatewayContext
from tracelens.security.budgets import BudgetCounterService


def estimate_tokens_from_messages(context: GatewayContext) -> tuple[int, int, int]:
    if context.chat_request is None:
        return 0, 0, 0
    words = sum(max(1, len(m.content.split())) for m in context.chat_request.messages)
    if context.chat_response is not None:
        usage = context.chat_response.usage
        return usage.prompt_tokens, usage.prompt_tokens, usage.completion_tokens
    return words, words, 0


async def persist_request_log(
    session: AsyncSession,
    context: GatewayContext,
    *,
    status: str = "completed",
    record_budget_usage: bool = True,
) -> None:
    if context.tenant_id is None or context.request_id is None:
        return
    if context.chat_request is None:
        return

    tokens_in_original, tokens_in_final, tokens_out = estimate_tokens_from_messages(context)
    cost_actual = Decimal("0")
    cost_without = Decimal("0")

    repo = RequestLogRepository(session, context.tenant_id)
    existing = await repo.get_by_request_id(context.request_id)
    if existing is not None:
        return

    row = await repo.create_row(
        api_key_id=context.key_id,
        request_id=context.request_id,
        model=context.chat_request.model,
        selected_model=context.selected_model,
        status=status,
        tokens_in_original=tokens_in_original,
        tokens_in_final=tokens_in_final,
        tokens_out=tokens_out,
        cost_actual=cost_actual,
        cost_without_optimization=cost_without,
        routing_explanation=dict(context.routing_explanation),
    )
    context.request_log_id = row.id

    if (
        not record_budget_usage
        or status != "completed"
        or context.key_id is None
        or context.budget_id is None
    ):
        return

    budget = await session.get(Budget, context.budget_id)
    if budget is None:
        return

    total_tokens = tokens_in_final + tokens_out
    redis = RedisClient.connection()
    counters = BudgetCounterService(redis)
    await counters.record_usage(
        budget,
        context.tenant_id,
        context.key_id,
        tokens=total_tokens,
        cost_usd=cost_actual,
    )


async def load_budget_for_context(session: AsyncSession, context: GatewayContext) -> Budget | None:
    if context.tenant_id is None or context.budget_id is None:
        return None
    budget = await session.get(Budget, context.budget_id)
    if budget is None or budget.tenant_id != context.tenant_id:
        return None
    return budget
