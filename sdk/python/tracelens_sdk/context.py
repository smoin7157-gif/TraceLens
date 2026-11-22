import uuid
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

_current_trace_id: ContextVar[str | None] = ContextVar("tracelens_trace_id", default=None)
_current_span_id: ContextVar[str | None] = ContextVar("tracelens_span_id", default=None)
_spans: ContextVar[list["SpanRecord"] | None] = ContextVar("tracelens_spans", default=None)


@dataclass
class SpanRecord:
    span_id: str
    parent_span_id: str | None
    name: str
    attrs: dict[str, Any] = field(default_factory=dict)


def _span_list() -> list[SpanRecord]:
    existing = _spans.get()
    if existing is None:
        existing = []
        _spans.set(existing)
    return existing


def current_trace() -> tuple[str | None, list[SpanRecord]]:
    return _current_trace_id.get(), list(_span_list())


@contextmanager
def trace_span(name: str, **attrs: Any) -> Generator[SpanRecord, None, None]:
    trace_id = _current_trace_id.get()
    if trace_id is None:
        trace_id = uuid.uuid4().hex
        _current_trace_id.set(trace_id)

    span_id = uuid.uuid4().hex[:16]
    parent = _current_span_id.get()
    token = _current_span_id.set(span_id)
    record = SpanRecord(span_id=span_id, parent_span_id=parent, name=name, attrs=dict(attrs))
    _span_list().append(record)
    try:
        yield record
    finally:
        if parent is None:
            _current_span_id.set(None)
        else:
            _current_span_id.reset(token)