from typing import Any

from fastapi import APIRouter

from tracelens.config import get_settings
from tracelens.db.redis_client import RedisClient
from tracelens.optimize.routing import provider_for_model
from tracelens.resilience.circuit_breaker import CircuitBreaker, circuit_scope_key
from tracelens.resilience.provider_stats import ProviderStats

router = APIRouter(tags=["health"])


@router.get("/health/providers")
async def provider_health() -> dict[str, Any]:
    """Provider/model circuit state and rolling stats for operations dashboard."""
    settings = get_settings()
    redis = RedisClient.connection()
    tenant_label = "system"

    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for model, _chain in settings.routing.fallback_chains.items():
        if model in seen:
            continue
        seen.add(model)
        provider = provider_for_model(model)
        scope = circuit_scope_key(tenant_label, provider, model)
        breaker = CircuitBreaker(redis, scope)
        stats = ProviderStats(redis, scope)
        try:
            circuit_state = await breaker.get_state()
            snapshot = await stats.snapshot()
            circuit_label = circuit_state.value
        except Exception:
            circuit_label = "unknown"
            snapshot = {"p95_latency_ms": 0.0, "error_rate": 0.0, "sample_count": 0}
        items.append(
            {
                "provider": provider,
                "model": model,
                "circuit_state": circuit_label,
                **snapshot,
            }
        )

    return {"object": "provider_health", "data": items}
