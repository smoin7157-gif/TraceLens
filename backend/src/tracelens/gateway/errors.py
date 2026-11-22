from typing import Any


class GatewayAuthError(Exception):
    def __init__(self, message: str, *, code: str = "invalid_api_key") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ProviderError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 500,
        code: str = "server_error",
        error_type: str = "server_error",
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.error_type = error_type
        self.retry_after_seconds = retry_after_seconds


class GatewayValidationError(Exception):
    def __init__(self, message: str, *, code: str = "invalid_request_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class GatewayRateLimitError(Exception):
    def __init__(self, message: str, *, code: str = "rate_limit_exceeded") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def openai_error_body(
    message: str,
    *,
    code: str = "invalid_api_key",
    error_type: str = "invalid_request_error",
    param: str | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "message": message,
            "type": error_type,
            "param": param,
            "code": code,
        }
    }
