from tracelens.config import get_settings
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


def estimate_message_tokens(messages: list[ChatMessage]) -> int:
    return sum(max(1, len(m.content.split())) for m in messages)


def compress_messages(messages: list[ChatMessage]) -> tuple[list[ChatMessage], list[str]]:
    """History trim + lightweight whitespace compression."""
    policy = get_settings().compress
    applied: list[str] = []
    trimmed = list(messages)

    if len(trimmed) > policy.max_history_messages:
        system = [m for m in trimmed if m.role == "system"]
        rest = [m for m in trimmed if m.role != "system"]
        keep_tail = max(1, policy.max_history_messages - len(system))
        trimmed = system + rest[-keep_tail:]
        applied.append("history_trim")

    if policy.collapse_whitespace:
        collapsed: list[ChatMessage] = []
        changed = False
        for message in trimmed:
            normalized = " ".join(message.content.split())
            if normalized != message.content:
                changed = True
            collapsed.append(message.model_copy(update={"content": normalized}))
        trimmed = collapsed
        if changed:
            applied.append("whitespace_compress")

    return trimmed, applied


def optimize_request(
    request: ChatCompletionRequest,
) -> tuple[ChatCompletionRequest, int, int, list[str]]:
    original_tokens = estimate_message_tokens(request.messages)
    compressed_messages, applied = compress_messages(request.messages)
    final_tokens = estimate_message_tokens(compressed_messages)
    optimized = request.model_copy(update={"messages": compressed_messages})
    return optimized, original_tokens, final_tokens, applied
