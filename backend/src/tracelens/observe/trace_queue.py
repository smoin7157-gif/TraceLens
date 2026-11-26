import json
import logging
import time

from fastapi import Request

from tracelens.config import get_settings
from tracelens.db.redis_client import RedisClient
from tracelens.observe.metrics import TRACE_ENQUEUE_DURATION, TRACE_ENQUEUE_TOTAL
from tracelens.observe.traces import build_gateway_trace_payload
from tracelens.pipeline.context import GatewayContext

logger = logging.getLogger(__name__)


async def enqueue_trace(request: Request, context: GatewayContext) -> None:
    """Push gateway trace payload to Redis (fail-open when configured)."""
    settings = get_settings().observe
    payload = build_gateway_trace_payload(request, context)
    if not payload:
        return

    started = time.perf_counter()
    try:
        redis = RedisClient.connection()
        await redis.lpush(
            settings.trace_queue_key,
            json.dumps(payload, default=str, separators=(",", ":")),
        )
        TRACE_ENQUEUE_TOTAL.labels(result="success").inc()
        context.metadata["trace_queue"] = settings.trace_queue_key
    except Exception:
        TRACE_ENQUEUE_TOTAL.labels(result="error").inc()
        logger.exception("trace_enqueue_failed_fail_open")
        if not settings.trace_enqueue_fail_open:
            raise
    finally:
        TRACE_ENQUEUE_DURATION.observe(time.perf_counter() - started)
