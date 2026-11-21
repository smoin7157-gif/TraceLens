from fastapi import Request

from tracelens.observe.trace_queue import enqueue_trace
from tracelens.pipeline.context import GatewayContext


class TraceEnqueueStage:
    name = "trace_enqueue"

    async def run(self, _request: Request, context: GatewayContext) -> None:
        await enqueue_trace(context)
        context.metadata["trace_enqueued"] = True
