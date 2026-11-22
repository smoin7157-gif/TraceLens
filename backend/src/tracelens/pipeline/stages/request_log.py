from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.observe.request_log import persist_request_log
from tracelens.optimize.cost import compute_economics
from tracelens.pipeline.context import GatewayContext


class RequestLogStage:
    name = "request_log"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run(self, _request: Request, context: GatewayContext) -> None:
        cost_actual, cost_without = compute_economics(context)
        context.cost_actual = cost_actual
        context.cost_without_optimization = cost_without
        await persist_request_log(self._session, context, status="completed")
