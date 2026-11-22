from tracelens_sdk import current_trace, trace_span, traced


def test_trace_span_creates_child_spans() -> None:
    with trace_span("parent"):
        with trace_span("child", key="v"):
            pass

    trace_id, spans = current_trace()
    assert trace_id is not None
    assert len(spans) == 2
    assert spans[0].name == "parent"
    assert spans[1].name == "child"
    assert spans[1].parent_span_id == spans[0].span_id


@traced("custom.fn")
def _sample(x: int) -> int:
    with trace_span("inner"):
        return x + 1


def test_traced_decorator_records_nested_span() -> None:
    assert _sample(1) == 2
    _trace_id, spans = current_trace()
    names = {s.name for s in spans}
    assert "custom.fn" in names
    assert "inner" in names
