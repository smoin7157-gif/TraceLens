from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.redis_client import RedisClient
from tracelens.optimize.cache import ExactCache, cache_prompt_digest
from tracelens.optimize.semantic import SemanticCache
from tracelens.pipeline.context import GatewayContext


class CacheWriteStage:
    name = "cache_write"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run(self, _request: Request, context: GatewayContext) -> None:
        if context.cache_bypass or context.cache_hit:
            return
        if (
            context.tenant_id is None
            or context.chat_request is None
            or context.chat_response is None
        ):
            return

        model = context.selected_model or context.chat_request.model
        messages = [
            m.model_dump(include={"role", "content"}) for m in context.chat_request.messages
        ]
        digest = cache_prompt_digest(messages, model)

        exact = ExactCache(RedisClient.connection())
        await exact.set(context.tenant_id, model, digest, context.chat_response)

        semantic = SemanticCache(self._session)
        await semantic.store(
            context.tenant_id,
            model,
            messages,
            digest,
            context.chat_response,
        )
        if "cache_write" not in context.optimizations_applied:
            context.optimizations_applied.append("cache_write")
