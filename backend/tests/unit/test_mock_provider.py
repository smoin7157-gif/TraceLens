import pytest
from starlette.requests import Request as StarletteRequest

from tracelens.gateway.errors import ProviderError
from tracelens.providers.mock import MockProvider
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


def _mock_http_request(*, error_rate: str, seed: int) -> StarletteRequest:
    scope = {
        "type": "http",
        "headers": [
            (b"x-tracelens-mock-error-rate", error_rate.encode()),
            (b"x-tracelens-mock-seed", str(seed).encode()),
            (b"x-tracelens-mock-latency-ms", b"0"),
        ],
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "client": ("127.0.0.1", 0),
        "server": ("test", 80),
    }
    return StarletteRequest(scope)


@pytest.mark.asyncio
async def test_mock_provider_seeded_error_rate() -> None:
    provider = MockProvider()
    request = ChatCompletionRequest(
        model="mock-gpt",
        messages=[ChatMessage(role="user", content="hello")],
    )

    successes = 0
    errors = 0
    for i in range(500):
        http_request = _mock_http_request(error_rate="0.4", seed=1000 + i)
        try:
            await provider.chat_completion(request, http_request=http_request)
            successes += 1
        except ProviderError:
            errors += 1

    assert 150 <= errors <= 250
    assert successes + errors == 500


@pytest.mark.asyncio
async def test_mock_provider_returns_openai_shape() -> None:
    provider = MockProvider()
    response = await provider.chat_completion(
        ChatCompletionRequest(
            model="mock-gpt-4",
            messages=[ChatMessage(role="user", content="ping")],
        ),
        http_request=None,
        completion_id="chatcmpl-test",
    )
    assert response.id == "chatcmpl-test"
    assert response.object == "chat.completion"
    assert response.choices[0].message.content.startswith("[mock:mock-gpt-4]")
