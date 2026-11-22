from fastapi import Request

from tracelens.gateway.errors import GatewayValidationError
from tracelens.optimize.complexity import complexity_score
from tracelens.optimize.compress import optimize_request
from tracelens.pipeline.context import GatewayContext


class OptimizerStage:
    name = "optimizer"

    async def run(self, _request: Request, context: GatewayContext) -> None:
        if context.chat_request is None:
            raise GatewayValidationError("Chat request missing on gateway context")

        optimized, tokens_in_original, tokens_in_final, applied = optimize_request(
            context.chat_request
        )
        context.chat_request = optimized
        context.tokens_in_original = tokens_in_original
        context.tokens_in_final = tokens_in_final
        context.complexity_score = complexity_score(optimized.messages)
        for tag in applied:
            if tag not in context.optimizations_applied:
                context.optimizations_applied.append(tag)
