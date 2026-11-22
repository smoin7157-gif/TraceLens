import time

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.redis_client import RedisClient
from tracelens.gateway.errors import GatewayValidationError, ProviderError
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.registry import ProviderRegistry
from tracelens.providers.retry import call_with_retry, retry_metadata
from tracelens.providers.router import resolve_provider_for_model
from tracelens.resilience.circuit_breaker import CircuitBreaker, circuit_scope_key
from tracelens.resilience.provider_stats import ProviderStats, stats_scope_key


class ProviderCallStage:
    name = "provider"

    def __init__(self, session: AsyncSession) -> None:
        self._registry = ProviderRegistry(session)

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.chat_request is None:
            raise GatewayValidationError("Chat request missing on gateway context")

        context.metadata.update(retry_metadata())
        candidates = context.route_candidates or [context.chat_request.model]
        tenant_label = str(context.tenant_id or "unknown")
        redis = RedisClient.connection()
        attempts: list[dict[str, object]] = []
        last_error: ProviderError | None = None

        for model in candidates:
            provider = resolve_provider_for_model(model)
            cb_scope = circuit_scope_key(tenant_label, provider, model)
            breaker = CircuitBreaker(redis, cb_scope)
            stats = ProviderStats(redis, stats_scope_key(tenant_label, provider, model))

            if not await breaker.allow_request():
                attempts.append({"model": model, "result": "circuit_open"})
                self._append_fallback(context, model, "circuit_open")
                continue

            started = time.perf_counter()
            request_for_model = context.chat_request.model_copy(update={"model": model})
            try:
                if context.chat_request.stream:
                    await self._registry.ensure_provider_ready(model)
                    context.stream_chunks = self._registry.chat_completion_stream(
                        request_for_model,
                        http_request=request,
                        completion_id=context.request_id,
                    )
                else:
                    context.chat_response = await call_with_retry(
                        self._registry.chat_completion,
                        request_for_model,
                        http_request=request,
                        completion_id=context.request_id,
                    )

                latency_ms = (time.perf_counter() - started) * 1000.0
                await breaker.record_success()
                await stats.record_success(latency_ms)
                context.selected_model = model
                attempts.append({"model": model, "result": "success", "latency_ms": latency_ms})
                context.routing_explanation["selected_model"] = model
                context.routing_explanation["attempts"] = attempts
                return
            except ProviderError as exc:
                last_error = exc
                await breaker.record_failure()
                await stats.record_failure()
                attempts.append(
                    {
                        "model": model,
                        "result": "provider_error",
                        "status_code": exc.status_code,
                        "retry_after_seconds": exc.retry_after_seconds,
                    }
                )
                if model != candidates[-1]:
                    self._append_fallback(context, model, f"error_{exc.status_code}")
                    continue
                raise

        context.routing_explanation["attempts"] = attempts
        if last_error is not None:
            raise last_error
        raise ProviderError(
            "All route candidates unavailable",
            status_code=503,
            code="model_unavailable",
            error_type="server_error",
        )

    @staticmethod
    def _append_fallback(context: GatewayContext, model: str, reason: str) -> None:
        events = context.routing_explanation.setdefault("fallback_events", [])
        events.append({"from": model, "reason": reason})
