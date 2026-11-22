from tracelens.optimize.routing import build_routing_plan


def test_high_quality_model_sorted_first() -> None:
    stats = {
        "mock-gpt": {"p95_latency_ms": 50.0, "error_rate": 0.0, "sample_count": 10},
        "mock-gpt-4": {"p95_latency_ms": 50.0, "error_rate": 0.0, "sample_count": 10},
    }
    ordered, explanation = build_routing_plan(
        "mock-gpt-4",
        stats,
        quality_by_model={"mock-gpt": 0.99, "mock-gpt-4": 0.4},
    )
    assert ordered[0] == "mock-gpt"
    assert explanation["eval_quality_score"] is not None
