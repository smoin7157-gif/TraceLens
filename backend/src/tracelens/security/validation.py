from fastapi import Request

from tracelens.config import get_settings
from tracelens.gateway.errors import GatewayValidationError
from tracelens.pipeline.context import GatewayContext


def validate_gateway_request(request: Request, context: GatewayContext) -> None:
    settings = get_settings()
    policy = settings.validation

    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            size = int(content_length)
        except ValueError as exc:
            raise GatewayValidationError("Invalid Content-Length header") from exc
        if size > policy.max_request_bytes:
            raise GatewayValidationError(
                f"Request payload too large (max {policy.max_request_bytes} bytes).",
                code="request_too_large",
            )

    chat_request = context.chat_request
    if chat_request is None:
        raise GatewayValidationError("Chat request missing on gateway context")

    if chat_request.max_tokens is not None and chat_request.max_tokens > policy.max_tokens_cap:
        raise GatewayValidationError(
            f"max_tokens exceeds cap of {policy.max_tokens_cap}",
            code="max_tokens_exceeded",
        )

    if context.allowed_models:
        if chat_request.model not in context.allowed_models:
            raise GatewayValidationError(
                f"The model `{chat_request.model}` does not exist or you do not have access to it.",
                code="model_not_found",
            )
