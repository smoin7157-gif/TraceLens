from tracelens.observe.evaluators import evaluate_output, run_regex_evaluator


def test_regex_evaluator_matches() -> None:
    score, _meta = run_regex_evaluator("hello TraceLens", r"tracelens")
    assert score == 1.0


def test_json_schema_evaluator_valid_object() -> None:
    score, meta = evaluate_output(
        "json_schema",
        {"schema": {"required": ["answer"], "properties": {"answer": {"type": "string"}}}},
        '{"answer": "42"}',
    )
    assert score == 1.0
    assert meta.get("type_ok") is True
