import httpx
import pytest

from tracelens.gateway.errors import ProviderError
from tracelens.providers import errors as provider_errors


def test_raise_from_http_parses_retry_after() -> None:
    response = httpx.Response(
        429,
        headers={"Retry-After": "12"},
        json={
            "error": {
                "message": "slow",
                "type": "rate_limit_error",
                "code": "rate_limit_exceeded",
            }
        },
    )
    with pytest.raises(ProviderError) as exc_info:
        provider_errors.raise_from_http_response(response)
    exc = exc_info.value
    assert exc.status_code == 429
    assert exc.retry_after_seconds == 12.0
