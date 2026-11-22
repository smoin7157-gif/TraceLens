from tracelens.observe.traces import format_traceparent, parse_traceparent


def test_parse_and_format_traceparent_round_trip() -> None:
    header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    parsed = parse_traceparent(header)
    assert parsed is not None
    assert parsed.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert parsed.parent_span_id == "00f067aa0ba902b7"
    assert (
        format_traceparent(parsed.trace_id, parsed.parent_span_id or "00f067aa0ba902b7") == header
    )
