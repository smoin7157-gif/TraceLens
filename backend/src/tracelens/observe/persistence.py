import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.trace import Span, Trace
from tracelens.db.repositories.trace import SpanRepository, TraceRepository
from tracelens.observe.span_ids import span_hex_to_uuid


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


async def persist_trace_payload(session: AsyncSession, payload: dict[str, Any]) -> Trace:
    tenant_id = uuid.UUID(str(payload["tenant_id"]))
    trace_repo = TraceRepository(session, tenant_id)
    existing = await trace_repo.get_by_trace_id(str(payload["trace_id"]))
    if existing is not None:
        return existing

    trace = await trace_repo.create_trace(
        trace_id=str(payload["trace_id"]),
        environment=str(payload.get("environment", "development")),
        tags=dict(payload.get("tags") or {}),
    )

    span_repo = SpanRepository(session, tenant_id)
    created: dict[str, uuid.UUID] = {}
    for item in payload.get("spans", []):
        raw_span_id = str(item["id"])
        span_id = span_hex_to_uuid(raw_span_id)
        parent_raw = item.get("parent_span_id")
        parent_uuid: uuid.UUID | None = None
        if parent_raw and str(parent_raw) in created:
            parent_uuid = created[str(parent_raw)]

        span = Span(
            id=span_id,
            tenant_id=tenant_id,
            trace_id=trace.id,
            parent_span_id=parent_uuid,
            kind=str(item.get("kind", "internal")),
            name=str(item["name"]),
            attrs=dict(item.get("attrs") or {}),
            started_at=_parse_ts(str(item["started_at"])),
            ended_at=_parse_ts(str(item["ended_at"])) if item.get("ended_at") else None,
        )
        await span_repo.add(span)
        created[raw_span_id] = span_id

    return trace
