import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.exceptions import TenantIsolationError
from tracelens.db.models.trace import Span, Trace
from tracelens.db.repositories.base import TenantScopedRepository


class TraceRepository(TenantScopedRepository[Trace]):
    model = Trace

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id)

    async def create_trace(
        self,
        *,
        trace_id: str,
        environment: str = "development",
        tags: dict[str, str] | None = None,
    ) -> Trace:
        trace = Trace(
            tenant_id=self.tenant_id,
            trace_id=trace_id,
            environment=environment,
            tags=tags or {},
        )
        return await self.add(trace)

    async def get_by_trace_id(self, trace_id: str) -> Trace | None:
        stmt = self._scoped_select().where(Trace.trace_id == trace_id)
        result = await self.session.execute(stmt)
        return cast(Trace | None, result.scalar_one_or_none())


class SpanRepository(TenantScopedRepository[Span]):
    model = Span

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        super().__init__(session, tenant_id)

    async def create_span(
        self,
        *,
        trace: Trace,
        kind: str,
        name: str,
        attrs: dict[str, object] | None = None,
        parent_span_id: uuid.UUID | None = None,
    ) -> Span:
        if trace.tenant_id != self.tenant_id:
            raise TenantIsolationError("Cannot attach span to another tenant's trace")
        now = datetime.now(UTC)
        span = Span(
            tenant_id=self.tenant_id,
            trace_id=trace.id,
            parent_span_id=parent_span_id,
            kind=kind,
            name=name,
            attrs=attrs or {},
            started_at=now,
        )
        return await self.add(span)
