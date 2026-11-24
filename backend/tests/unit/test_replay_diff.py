from tracelens.observe.replay import diff_replay, normalize_completion_text
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


def _response(text: str) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id="chatcmpl-test",
        created=1,
        model="mock-gpt",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=text),
                finish_reason="stop",
            )
        ],
        usage=CompletionUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
    )


def test_replay_diff_identical() -> None:
    result = diff_replay(
        original_text="[mock:mock-gpt] hello",
        replay_response=_response("[mock:mock-gpt] hello"),
    )
    assert result["identical"] is True


def test_replay_diff_whitespace_insensitive() -> None:
    assert normalize_completion_text("a  b") == "a b"
    result = diff_replay(
        original_text="same   text",
        replay_response=_response("same text"),
    )
    assert result["identical"] is True
