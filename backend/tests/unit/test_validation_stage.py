import pytest
from starlette.requests import Request as StarletteRequest

from tracelens.gateway.errors import GatewayValidationError
from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.stages.validation import ValidationStage
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


def _request(content_length: str | None = None) -> StarletteRequest:
    headers: list[tuple[bytes, bytes]] = []
    if content_length is not None:
        headers.append((b"content-length", content_length.encode()))
    scope = {
        "type": "http",
        "headers": headers,
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "client": ("127.0.0.1", 0),
        "server": ("test", 80),
    }
    return StarletteRequest(scope)


@pytest.mark.asyncio
async def test_validation_rejects_disallowed_model() -> None:
    context = GatewayContext(
        allowed_models=["mock-gpt"],
        chat_request=ChatCompletionRequest(
            model="gpt-4o",
            messages=[ChatMessage(role="user", content="hi")],
        ),
    )
    with pytest.raises(GatewayValidationError) as exc:
        await ValidationStage().run(_request("128"), context)
    assert exc.value.code == "model_not_found"


@pytest.mark.asyncio
async def test_validation_rejects_oversized_payload() -> None:
    context = GatewayContext(
        chat_request=ChatCompletionRequest(
            model="mock-gpt",
            messages=[ChatMessage(role="user", content="hi")],
        ),
    )
    with pytest.raises(GatewayValidationError) as exc:
        await ValidationStage().run(_request("5000000"), context)
    assert exc.value.code == "request_too_large"
