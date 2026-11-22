from fastapi import Request

from tracelens.pipeline.context import GatewayContext
from tracelens.security.validation import validate_gateway_request


class ValidationStage:
    name = "validation"

    async def run(self, request: Request, context: GatewayContext) -> None:
        validate_gateway_request(request, context)
