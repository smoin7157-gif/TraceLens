import httpx

from tracelens.gateway.errors import ProviderError


def _parse_retry_after(response: httpx.Response) -> float | None:
    header = response.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return float(header)
    except ValueError:
        return None


def raise_from_http_response(response: httpx.Response) -> None:
    retry_after = _parse_retry_after(response)
    try:
        body = response.json()
        msg = body.get("error", {}).get("message", response.text)
        code = body.get("error", {}).get("code", "provider_error")
        error_type = body.get("error", {}).get("type", "server_error")
    except Exception:
        msg = response.text
        code = "provider_error"
        error_type = "server_error"
    if response.status_code == 429:
        raise ProviderError(
            msg,
            status_code=429,
            code=code or "rate_limit_exceeded",
            error_type="rate_limit_error",
            retry_after_seconds=retry_after,
        )
    raise ProviderError(
        msg,
        status_code=response.status_code,
        code=code,
        error_type=error_type,
        retry_after_seconds=retry_after,
    )
