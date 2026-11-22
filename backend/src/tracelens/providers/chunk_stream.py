import time
from collections.abc import AsyncIterator
from typing import Any

from tracelens.providers.schemas import ChatCompletionRequest
from tracelens.providers.streaming import make_chat_chunk


async def stream_text_as_openai_chunks(
    request: ChatCompletionRequest,
    *,
    completion_id: str,
    full_text: str,
) -> AsyncIterator[dict[str, Any]]:
    created = int(time.time())
    yield make_chat_chunk(
        completion_id=completion_id,
        model=request.model,
        created=created,
        delta_role="assistant",
    )

    parts = full_text.split(" ")
    for index, word in enumerate(parts):
        suffix = "" if index == len(parts) - 1 else " "
        yield make_chat_chunk(
            completion_id=completion_id,
            model=request.model,
            created=created,
            delta_content=word + suffix,
        )

    yield make_chat_chunk(
        completion_id=completion_id,
        model=request.model,
        created=created,
        finish_reason="stop",
    )
