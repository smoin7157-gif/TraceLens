from tracelens.observe.shadow import should_shadow


def test_shadow_sampling_deterministic() -> None:
    assert should_shadow(request_id="req-a", sample_rate=0.0) is False
    assert should_shadow(request_id="req-a", sample_rate=1.0) is True
    first = should_shadow(request_id="stable-id-123", sample_rate=0.5)
    second = should_shadow(request_id="stable-id-123", sample_rate=0.5)
    assert first == second


def test_shadow_sampling_rate_boundary() -> None:
    hits = sum(1 for idx in range(200) if should_shadow(request_id=f"id-{idx}", sample_rate=0.25))
    assert 20 <= hits <= 80
