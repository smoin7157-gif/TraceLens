from tracelens.optimize.compress import compress_messages, optimize_request
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


def test_history_trim_reduces_tokens() -> None:
    messages = [ChatMessage(role="user", content=f"msg-{i}") for i in range(30)]
    compressed, applied = compress_messages(messages)
    assert "history_trim" in applied
    assert len(compressed) < len(messages)


def test_optimizer_records_original_and_final_tokens() -> None:
    request = ChatCompletionRequest(
        model="mock-gpt",
        messages=[ChatMessage(role="user", content="  hello   world  ")],
    )
    optimized, original, final, applied = optimize_request(request)
    assert original >= final
    assert optimized.messages[0].content == "hello world"
    assert "whitespace_compress" in applied
