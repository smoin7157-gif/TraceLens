import uuid

from redis.asyncio import Redis


def quality_score_key(tenant_id: uuid.UUID, model: str) -> str:
    return f"tl:quality:{tenant_id}:{model}"


async def get_quality_scores(
    redis: Redis,
    tenant_id: uuid.UUID,
    models: list[str],
) -> dict[str, float]:
    if not models:
        return {}
    keys = [quality_score_key(tenant_id, model) for model in models]
    values = await redis.mget(*keys)
    out: dict[str, float] = {}
    for model, raw in zip(models, values, strict=True):
        if raw is None:
            continue
        try:
            out[model] = float(str(raw))
        except ValueError:
            continue
    return out


async def set_quality_score(
    redis: Redis,
    tenant_id: uuid.UUID,
    model: str,
    score: float,
) -> None:
    await redis.set(quality_score_key(tenant_id, model), str(score), ex=60 * 60 * 24 * 7)
