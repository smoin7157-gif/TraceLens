import json

import pytest
import respx
from httpx import Response

from tracelens.providers.openai import OpenAIProvider
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


@pytest.mark.asyncio
@respx.mock
async def test_openai_stream_passthrough_chunks() -> None:
    chunk_json = json.dumps(
        {
            "id": "chatcmpl-x",
            "object": "chat.completion.chunk",
            "choices": [{"delta": {"content": "hi"}}],
        }
    )
    sse_body = f"data: {chunk_json}\n\ndata: [DONE]\n\n"
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(200, content=sse_body)
    )

    provider = OpenAIProvider("sk-test")
    chunks = []
    async for chunk in provider.chat_completion_stream(
        ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="hello")],
        ),
        completion_id="chatcmpl-override",
    ):
        chunks.append(chunk)

    assert chunks
    assert chunks[0]["object"] == "chat.completion.chunk"
    assert chunks[0]["id"] == "chatcmpl-override"
    assert chunks[0]["choices"][0]["delta"]["content"] == "hi"
