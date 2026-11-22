import time
from typing import Any, Literal


def make_chat_chunk(
    *,
    completion_id: str,
    model: str,
    created: int | None = None,
    delta_content: str | None = None,
    delta_role: Literal["assistant"] | None = None,
    finish_reason: Literal["stop", "length"] | None = None,
) -> dict[str, Any]:
    delta: dict[str, str] = {}
    if delta_role is not None:
        delta["role"] = delta_role
    if delta_content is not None:
        delta["content"] = delta_content
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created or int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }
