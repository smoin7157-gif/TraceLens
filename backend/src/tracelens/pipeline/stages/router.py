from fastapi import Request

from tracelens.config import get_settings
from tracelens.db.redis_client import RedisClient
from tracelens.gateway.errors import GatewayValidationError
from tracelens.optimize.routing import build_routing_plan, provider_for_model
from tracelens.pipeline.context import GatewayContext
from tracelens.resilience.provider_stats import ProviderStats, stats_scope_key


class RouterStage:
    name = "router"

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.chat_request is None:
            raise GatewayValidationError("Chat request missing on gateway context")

        tenant_label = str(context.tenant_id or "unknown")
        requested = context.chat_request.model
        context.requested_model = requested
        chain_models = get_settings().routing.fallback_chains.get(requested, [requested])

        stats_by_model: dict[str, dict[str, float | int]] = {}
        redis = RedisClient.connection()
        for model in chain_models:
            provider = provider_for_model(model)
            stats = ProviderStats(redis, stats_scope_key(tenant_label, provider, model))
            try:
                stats_by_model[model] = await stats.snapshot()
            except Exception:
                stats_by_model[model] = {
                    "p95_latency_ms": 50.0,
                    "error_rate": 0.0,
                    "sample_count": 0,
                }

        ordered, explanation = build_routing_plan(requested, stats_by_model)
        context.route_candidates = ordered
        context.routing_explanation = explanation
        context.selected_model = ordered[0]
