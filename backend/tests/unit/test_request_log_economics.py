from tracelens.observe.request_log import estimate_tokens_from_messages
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


def test_estimate_tokens_from_completion_response() -> None:
    context = GatewayContext(
        chat_request=ChatCompletionRequest(
            model="mock-gpt",
            messages=[ChatMessage(role="user", content="hello world")],
        ),
        chat_response=ChatCompletionResponse(
            id="x",
            created=1,
            model="mock-gpt",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="hi"),
                )
            ],
            usage=CompletionUsage(prompt_tokens=3, completion_tokens=2, total_tokens=5),
        ),
    )
    original, final, out = estimate_tokens_from_messages(context)
    assert original == 3
    assert final == 3
    assert out == 2
