import pytest
from starlette.requests import Request

from tracelens.gateway.errors import ProviderError
from tracelens.providers.mock import MockProvider
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


def _request_with_headers(headers: list[tuple[bytes, bytes]]) -> Request:
    scope = {
        "type": "http",
        "headers": headers,
        "method": "POST",
        "path": "/",
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_mock_errors_only_on_listed_models() -> None:
    provider = MockProvider()
    http_request = _request_with_headers(
        [
            (b"x-tracelens-mock-error-rate", b"1.0"),
            (b"x-tracelens-mock-error-models", b"mock-gpt"),
            (b"x-tracelens-mock-seed", b"42"),
        ]
    )
    failing = ChatCompletionRequest(
        model="mock-gpt",
        messages=[ChatMessage(role="user", content="hi")],
    )
    with pytest.raises(ProviderError):
        await provider.chat_completion(failing, http_request=http_request)

    ok = ChatCompletionRequest(
        model="mock-gpt-4",
        messages=[ChatMessage(role="user", content="hi")],
    )
    response = await provider.chat_completion(ok, http_request=http_request)
    assert "mock-gpt-4" in response.choices[0].message.content
