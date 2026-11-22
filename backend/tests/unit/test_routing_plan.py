from tracelens.optimize.routing import build_routing_plan, fallback_chain_for_model


def test_fallback_chain_includes_primary_model() -> None:
    chain = fallback_chain_for_model("mock-gpt")
    assert chain[0] == "mock-gpt"
    assert "mock-gpt-4" in chain


def test_build_routing_plan_orders_by_health() -> None:
    stats = {
        "mock-gpt": {"p95_latency_ms": 200.0, "error_rate": 0.5, "sample_count": 10},
        "mock-gpt-4": {"p95_latency_ms": 20.0, "error_rate": 0.0, "sample_count": 10},
    }
    ordered, explanation = build_routing_plan("mock-gpt", stats)
    assert ordered[0] == "mock-gpt-4"
    assert explanation["requested_model"] == "mock-gpt"
    assert explanation["candidates"] == ["mock-gpt", "mock-gpt-4"]
