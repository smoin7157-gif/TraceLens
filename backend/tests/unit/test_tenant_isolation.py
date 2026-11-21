import uuid
from unittest.mock import MagicMock

import pytest

from tracelens.db.exceptions import TenantIsolationError
from tracelens.db.models.trace import Trace
from tracelens.db.repositories.trace import SpanRepository, TraceRepository


def test_prepare_create_rejects_foreign_tenant_id() -> None:
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    repo = TraceRepository(session=MagicMock(), tenant_id=tenant_a)

    with pytest.raises(TenantIsolationError):
        repo._prepare_create({"tenant_id": tenant_b, "trace_id": "abc"})


def test_assert_tenant_owned_raises_on_mismatch() -> None:
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    repo = TraceRepository(session=MagicMock(), tenant_id=tenant_a)
    foreign_trace = Trace(tenant_id=tenant_b, trace_id="x", environment="test", tags={})

    with pytest.raises(TenantIsolationError):
        repo._assert_tenant_owned(foreign_trace)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cross_tenant_trace_read_blocked(db_session) -> None:
    from tracelens.db.repositories.tenant import TenantRepository

    tenants = TenantRepository(db_session)
    alpha = await tenants.create(name="Alpha", slug=f"alpha-{uuid.uuid4().hex[:8]}")
    beta = await tenants.create(name="Beta", slug=f"beta-{uuid.uuid4().hex[:8]}")
    await db_session.commit()

    traces_a = TraceRepository(db_session, alpha.id)
    trace = await traces_a.create_trace(trace_id="trace-shared-id", tags={"app": "hire-ai"})
    await db_session.commit()

    traces_b = TraceRepository(db_session, beta.id)
    assert await traces_b.get_by_id(trace.id) is None
    assert await traces_b.get_by_trace_id("trace-shared-id") is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_span_cannot_attach_to_foreign_trace(db_session) -> None:
    from tracelens.db.repositories.tenant import TenantRepository

    tenants = TenantRepository(db_session)
    alpha = await tenants.create(name="Alpha", slug=f"alpha-{uuid.uuid4().hex[:8]}")
    beta = await tenants.create(name="Beta", slug=f"beta-{uuid.uuid4().hex[:8]}")
    await db_session.commit()

    trace = await TraceRepository(db_session, alpha.id).create_trace(trace_id="t1")
    await db_session.commit()

    spans_b = SpanRepository(db_session, beta.id)
    with pytest.raises(TenantIsolationError):
        await spans_b.create_span(trace=trace, kind="llm", name="completion")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_model_crud_smoke(db_session) -> None:
    from tracelens.db.models.api_key import ApiKey
    from tracelens.db.repositories.tenant import TenantRepository

    tenant = await TenantRepository(db_session).create(
        name="Demo",
        slug=f"demo-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(
        ApiKey(
            tenant_id=tenant.id,
            key_hash="hash",
            key_prefix="tl_abc",
            name="default",
            scopes=["gateway"],
            allowed_models=["gpt-4o-mini"],
        )
    )
    await db_session.commit()

    traces = TraceRepository(db_session, tenant.id)
    trace = await traces.create_trace(trace_id="smoke", environment="test")
    span = await SpanRepository(db_session, tenant.id).create_span(
        trace=trace,
        kind="llm",
        name="chat",
        attrs={"model": "mock"},
    )
    await db_session.commit()

    loaded = await traces.get_by_trace_id("smoke")
    assert loaded is not None
    assert loaded.id == trace.id
    assert span.tenant_id == tenant.id
