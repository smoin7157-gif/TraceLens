from typing import Protocol

from fastapi import Request

from tracelens.pipeline.context import GatewayContext


class PipelineStage(Protocol):
    name: str

    async def run(self, request: Request, context: GatewayContext) -> None: ...
