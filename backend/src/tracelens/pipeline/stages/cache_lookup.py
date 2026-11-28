from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.redis_client import RedisClient
from tracelens.gateway.errors import GatewayValidationError
from tracelens.observe.metrics import CACHE_LOOKUP_TOTAL
from tracelens.optimize.cache import ExactCache, cache_prompt_digest
from tracelens.optimize.semantic import SemanticCache
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.chunk_stream import stream_text_as_openai_chunks


class CacheLookupStage:
    name = "cache_lookup"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.chat_request is None or context.tenant_id is None:
            raise GatewayValidationError("Chat request missing on gateway context")

        bypass = request.headers.get("X-TraceLens-Cache-Bypass", "").lower() in {
            "1",
            "true",
            "yes",
        }
        context.cache_bypass = bypass
        if bypass:
            context.cache_status = "bypass"
            CACHE_LOOKUP_TOTAL.labels(kind="bypass").inc()
            return

        model = context.selected_model or context.chat_request.model
        messages = [
            m.model_dump(include={"role", "content"}) for m in context.chat_request.messages
        ]
        digest = cache_prompt_digest(messages, model)

        exact = ExactCache(RedisClient.connection())
        hit = await exact.get(context.tenant_id, model, digest)
        if hit is not None:
            context.cache_hit = True
            context.cache_status = "exact"
            CACHE_LOOKUP_TOTAL.labels(kind="exact").inc()
            context.chat_response = hit.model_copy(update={"id": context.request_id or hit.id})
            context.tokens_out = hit.usage.completion_tokens
            await self._attach_stream_if_needed(request, context, hit)
            context.metadata["cache_similarity"] = 1.0
            return

        semantic = SemanticCache(self._session)
        near, score = await semantic.lookup(context.tenant_id, model, messages)
        if near is not None:
            context.cache_hit = True
            context.cache_status = "semantic"
            CACHE_LOOKUP_TOTAL.labels(kind="semantic").inc()
            context.chat_response = near.model_copy(update={"id": context.request_id or near.id})
            context.tokens_out = near.usage.completion_tokens
            context.metadata["cache_similarity"] = score
            await self._attach_stream_if_needed(request, context, near)
            if "semantic_cache" not in context.optimizations_applied:
                context.optimizations_applied.append("semantic_cache")
            return

        context.cache_status = "miss"
        CACHE_LOOKUP_TOTAL.labels(kind="miss").inc()
        context.metadata["cache_digest"] = digest

    async def _attach_stream_if_needed(
        self,
        request: Request,
        context: GatewayContext,
        response: object,
    ) -> None:
        if context.chat_request is None or not context.chat_request.stream:
            return
        from tracelens.providers.schemas import ChatCompletionResponse

        if not isinstance(response, ChatCompletionResponse):
            return
        text = response.choices[0].message.content
        context.stream_chunks = stream_text_as_openai_chunks(
            context.chat_request,
            completion_id=response.id,
            full_text=text,
        )
        _ = request
