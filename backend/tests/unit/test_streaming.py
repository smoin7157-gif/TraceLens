import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.gateway.streaming import format_sse_data, iter_sse_chunks
from tracelens.main import app


@pytest.mark.asyncio
async def test_format_sse_openai_chunk() -> None:
    line = format_sse_data({"object": "chat.completion.chunk", "choices": []})
    assert line.startswith("data: ")
    assert line.endswith("\n\n")
    assert json.loads(line.removeprefix("data: ").strip())["object"] == "chat.completion.chunk"


@pytest.mark.asyncio
async def test_iter_sse_chunks_stops_on_disconnect() -> None:
    async def chunks():
        for i in range(10):
            yield {"index": i}

    request = MagicMock()
    request.is_disconnected = AsyncMock(side_effect=[False, False, True])

    collected: list[str] = []
    async for event in iter_sse_chunks(request, chunks()):
        collected.append(event)

    assert len(collected) == 2


@pytest.mark.asyncio
async def test_chat_stream_requires_auth() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "mock-gpt",
                "stream": True,
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
    assert response.status_code == 401
