import json
import logging
import uuid

from tracelens.config import get_settings
from tracelens.db.redis_client import RedisClient

logger = logging.getLogger(__name__)


async def enqueue_eval_job(
    *,
    tenant_id: uuid.UUID,
    evaluator_id: uuid.UUID,
    target_id: str,
    output_text: str,
    model: str | None = None,
    experiment_id: uuid.UUID | None = None,
    prompt_version_id: uuid.UUID | None = None,
) -> None:
    settings = get_settings().observe
    payload = {
        "tenant_id": str(tenant_id),
        "evaluator_id": str(evaluator_id),
        "target_id": target_id,
        "output_text": output_text,
        "model": model,
        "experiment_id": str(experiment_id) if experiment_id else None,
        "prompt_version_id": str(prompt_version_id) if prompt_version_id else None,
    }
    try:
        redis = RedisClient.connection()
        await redis.lpush(settings.eval_queue_key, json.dumps(payload))
    except Exception:
        logger.exception("eval_enqueue_fail_open")
