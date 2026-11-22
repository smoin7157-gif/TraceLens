import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from tracelens.db.models.trace import Span
from tracelens.observe.persistence import persist_trace_payload


@pytest.mark.integration
@pytest.mark.asyncio
async def test_span_parent_child_integrity(db_session) -> None:
    tenant_id = uuid.uuid4()
    root_span = uuid.uuid4().hex[:16]
    child_span = uuid.uuid4().hex[:16]
    now = datetime.now(UTC).isoformat()
    payload = {
        "tenant_id": str(tenant_id),
        "trace_id": uuid.uuid4().hex,
        "environment": "test",
        "tags": {},
        "spans": [
            {
                "id": root_span,
                "parent_span_id": None,
                "kind": "server",
                "name": "gateway.chat",
                "attrs": {},
                "started_at": now,
                "ended_at": now,
            },
            {
                "id": child_span,
                "parent_span_id": root_span,
                "kind": "internal",
                "name": "pipeline.provider",
                "attrs": {},
                "started_at": now,
                "ended_at": now,
            },
        ],
    }

    from tracelens.db.models.tenant import Tenant

    tenant = Tenant(id=tenant_id, name="trace", slug=f"tr-{tenant_id.hex[:6]}")
    db_session.add(tenant)
    await db_session.flush()

    await persist_trace_payload(db_session, payload)
    await db_session.commit()

    result = await db_session.execute(select(Span).where(Span.tenant_id == tenant_id))
    spans = list(result.scalars().all())
    assert len(spans) == 2
    child = next(s for s in spans if s.name == "pipeline.provider")
    root = next(s for s in spans if s.name == "gateway.chat")
    assert child.parent_span_id == root.id
