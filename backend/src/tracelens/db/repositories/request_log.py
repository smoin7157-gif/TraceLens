import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.request_log import RequestLog
from tracelens.db.repositories.base import TenantScopedRepository


class RequestLogRepository(TenantScopedRepository[RequestLog]):
    model = RequestLog

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id)

    async def create_row(
        self,
        *,
        api_key_id: uuid.UUID | None,
        request_id: str,
        model: str,
        selected_model: str | None,
        status: str,
        tokens_in_original: int,
        tokens_in_final: int,
        tokens_out: int,
        cost_actual: Decimal,
        cost_without_optimization: Decimal,
        cache_status: str,
        optimizations_applied: list[str],
        routing_explanation: dict[str, object],
        request_payload: dict[str, object] | None = None,
    ) -> RequestLog:
        entity = RequestLog(
            tenant_id=self.tenant_id,
            api_key_id=api_key_id,
            request_id=request_id,
            model=model,
            selected_model=selected_model,
            status=status,
            tokens_in_original=tokens_in_original,
            tokens_in_final=tokens_in_final,
            tokens_out=tokens_out,
            cost_actual=cost_actual,
            cost_without_optimization=cost_without_optimization,
            cache_status=cache_status,
            optimizations_applied=optimizations_applied,
            routing_explanation=routing_explanation,
            request_payload=request_payload or {},
        )
        return await self.add(entity)

    async def get_by_request_id(self, request_id: str) -> RequestLog | None:
        stmt = select(RequestLog).where(
            RequestLog.tenant_id == self.tenant_id,
            RequestLog.request_id == request_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
