from tracelens.gateway.errors import (
    OPENAI_ERROR_MAP,
    GatewayBudgetError,
    GatewayRateLimitError,
)


def test_budget_error_maps_to_insufficient_quota() -> None:
    status, code, error_type = OPENAI_ERROR_MAP[GatewayBudgetError]
    assert status == 429
    assert code == "insufficient_quota"
    assert error_type == "insufficient_quota"


def test_rate_limit_entry_unchanged() -> None:
    status, code, error_type = OPENAI_ERROR_MAP[GatewayRateLimitError]
    assert code == "rate_limit_exceeded"
