import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.api.dashboard import _build_span_tree
from tracelens.db.models.tenant import Tenant
from tracelens.db.models.trace import Span, Trace
from tracelens.main import app


def test_build_span_tree_parent_child() -> None:
    root_id = uuid.uuid4()
    child_id = uuid.uuid4()
    tenant = uuid.uuid4()
    trace_id = uuid.uuid4()
    now = datetime.now(UTC)
    root = Span(
        id=root_id,
        tenant_id=tenant,
        trace_id=trace_id,
        parent_span_id=None,
        kind="server",
        name="gateway.chat",
        attrs={},
        started_at=now,
        ended_at=now,
    )
    child = Span(
        id=child_id,
        tenant_id=tenant,
        trace_id=trace_id,
        parent_span_id=root_id,
        kind="internal",
        name="pipeline.provider",
        attrs={},
        started_at=now,
        ended_at=now,
    )
    tree = _build_span_tree([root, child])
    assert len(tree) == 1
    assert tree[0]["children"][0]["name"] == "pipeline.provider"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dashboard_list_traces(db_session) -> None:
    tenant_id = uuid.uuid4()
    db_session.add(Tenant(id=tenant_id, name="Dash", slug=f"d-{tenant_id.hex[:6]}"))
    trace = Trace(
        tenant_id=tenant_id,
        trace_id="trace-demo-1",
        environment="test",
        tags={},
    )
    db_session.add(trace)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/dashboard/traces?tenant_id={tenant_id}")
    assert response.status_code == 200
    assert response.json()["data"][0]["trace_id"] == "trace-demo-1"
