from tracelens.observe.live_metrics import record_gateway_outcome, snapshot


def test_live_metrics_snapshot_success_rate() -> None:
    record_gateway_outcome("success")
    record_gateway_outcome("success")
    record_gateway_outcome("auth_error")
    data = snapshot(window_seconds=3600)
    assert data["sample_count"] >= 3.0
    assert 0.0 < data["success_rate"] < 1.0
