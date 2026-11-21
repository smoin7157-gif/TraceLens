from typing import Any


class GatewayAuthError(Exception):
    def __init__(self, message: str, *, code: str = "invalid_api_key") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def openai_error_body(message: str, *, code: str = "invalid_api_key") -> dict[str, Any]:
    return {
        "error": {
            "message": message,
            "type": "invalid_request_error",
            "param": None,
            "code": code,
        }
    }
