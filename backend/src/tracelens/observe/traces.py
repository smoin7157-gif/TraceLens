import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import Request

from tracelens.config import get_settings
from tracelens.pipeline.context import GatewayContext

_TRACEPARENT_RE = re.compile(
    r"^[\da-f]{2}-([\da-f]{32})-([\da-f]{16})-([\da-f]{2})$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    parent_span_id: str | None
    sampled: bool


def parse_traceparent(header: str | None) -> TraceContext | None:
    if not header:
        return None
    header = header.strip()
    match = _TRACEPARENT_RE.match(header)
    if not match:
        return None
    trace_id, parent_id, _flags = match.groups()
    return TraceContext(
        trace_id=trace_id.lower(),
        parent_span_id=parent_id.lower(),
        sampled=True,
    )


def new_trace_id() -> str:
    return uuid.uuid4().hex


def new_span_id() -> str:
    return uuid.uuid4().hex[:16]


def format_traceparent(trace_id: str, span_id: str, *, sampled: bool = True) -> str:
    flags = "01" if sampled else "00"
    return f"00-{trace_id}-{span_id}-{flags}"


def init_trace_context(request: Request, context: GatewayContext) -> None:
    parsed = parse_traceparent(request.headers.get("traceparent"))
    if parsed is not None:
        context.trace_id = parsed.trace_id
        context.parent_span_id = parsed.parent_span_id
    else:
        context.trace_id = new_trace_id()
        context.parent_span_id = None
    context.root_span_id = new_span_id()
    if context.started_at is None:
        context.started_at = datetime.now(UTC)


def build_gateway_trace_payload(request: Request, context: GatewayContext) -> dict[str, Any]:
    if context.tenant_id is None or context.trace_id is None or context.root_span_id is None:
        return {}

    settings = get_settings()
    ended = datetime.now(UTC)
    started = context.started_at or ended

    root_attrs: dict[str, object] = {
        "http.method": request.method,
        "http.route": "/v1/chat/completions",
        "request_id": context.request_id,
        "cache_status": context.cache_status,
        "stages": list(context.stages_executed),
    }
    if context.parent_span_id:
        root_attrs["w3c.parent_span_id"] = context.parent_span_id

    spans: list[dict[str, Any]] = [
        {
            "id": context.root_span_id,
            "parent_span_id": context.parent_span_id,
            "kind": "server",
            "name": "gateway.chat",
            "attrs": root_attrs,
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
        }
    ]

    for stage in context.stages_executed:
        child_id = new_span_id()
        spans.append(
            {
                "id": child_id,
                "parent_span_id": context.root_span_id,
                "kind": "internal",
                "name": f"pipeline.{stage}",
                "attrs": {"stage": stage},
                "started_at": started.isoformat(),
                "ended_at": ended.isoformat(),
            }
        )

    return {
        "tenant_id": str(context.tenant_id),
        "trace_id": context.trace_id,
        "environment": settings.app_env,
        "tags": {
            "model": context.chat_request.model if context.chat_request else "",
            "selected_model": context.selected_model or "",
        },
        "spans": spans,
    }
