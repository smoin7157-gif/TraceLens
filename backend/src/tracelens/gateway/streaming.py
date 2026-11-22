import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request

from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.stages.trace_enqueue import TraceEnqueueStage

SSE_DONE = "data: [DONE]\n\n"


def format_sse_data(payload: dict[str, Any] | str) -> str:
    if payload == "[DONE]":
        return SSE_DONE
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def iter_sse_chunks(
    request: Request,
    chunks: AsyncIterator[dict[str, Any]],
) -> AsyncIterator[str]:
    """Yield OpenAI-style SSE lines; stop when the client disconnects."""
    client_disconnected = False
    async for chunk in chunks:
        if await request.is_disconnected():
            client_disconnected = True
            break
        yield format_sse_data(chunk)
    if not client_disconnected:
        yield SSE_DONE


async def stream_chat_response(
    request: Request,
    context: GatewayContext,
    chunks: AsyncIterator[dict[str, Any]],
) -> AsyncIterator[str]:
    """Stream SSE to the client, then run trace enqueue after the stream ends."""
    try:
        async for line in iter_sse_chunks(request, chunks):
            yield line
    finally:
        trace_stage = TraceEnqueueStage()
        await trace_stage.run(request, context)
        if "trace_enqueue" not in context.stages_executed:
            context.stages_executed.append("trace_enqueue")
