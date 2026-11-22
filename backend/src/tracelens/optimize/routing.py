from typing import Any

from tracelens.config import get_settings
from tracelens.providers.router import resolve_provider_for_model


def fallback_chain_for_model(model: str) -> list[str]:
    settings = get_settings()
    chain = settings.routing.fallback_chains.get(model)
    if chain:
        return list(chain)
    return [model]


def rank_models_by_health(
    models: list[str],
    stats_by_model: dict[str, dict[str, float | int]],
) -> list[str]:
    """Order models by weighted health score (lower is better)."""
    settings = get_settings()
    weights = settings.routing

    def score(model: str) -> float:
        stats = stats_by_model.get(model, {})
        p95 = float(stats.get("p95_latency_ms", 50.0))
        error_rate = float(stats.get("error_rate", 0.0))
        cost = 1.0 if model.startswith("mock-") else 2.0
        quality = 0.8
        return (
            weights.weight_latency * p95
            + weights.weight_error * (error_rate * 1000.0)
            + weights.weight_cost * cost
            + weights.weight_quality * (1.0 - quality) * 100.0
        )

    return sorted(models, key=score)


def build_routing_plan(
    requested_model: str,
    stats_by_model: dict[str, dict[str, float | int]],
) -> tuple[list[str], dict[str, Any]]:
    candidates = fallback_chain_for_model(requested_model)
    ordered = rank_models_by_health(candidates, stats_by_model)
    explanation = {
        "requested_model": requested_model,
        "candidates": candidates,
        "ordered_by_health": ordered,
        "eval_quality_score": None,
        "weights": get_settings().routing.model_dump(
            include={"weight_latency", "weight_error", "weight_cost", "weight_quality"}
        ),
    }
    return ordered, explanation


def provider_for_model(model: str) -> str:
    return resolve_provider_for_model(model)
