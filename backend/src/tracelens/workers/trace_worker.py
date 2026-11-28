import asyncio
import json
import logging

from tracelens.config import get_settings
from tracelens.db.redis_client import RedisClient
from tracelens.db.session import async_session_factory, dispose_engine
from tracelens.observe.metrics import TRACE_DLQ_TOTAL, TRACE_WORKER_PROCESSED
from tracelens.observe.persistence import persist_trace_payload

logger = logging.getLogger(__name__)


async def process_queue_once() -> int:
    settings = get_settings().observe
    redis = RedisClient.connection()
    processed = 0
    factory = async_session_factory()

    batch = await redis.rpop(settings.trace_queue_key, count=settings.worker_batch_size)
    if not batch:
        return 0
    items = batch if isinstance(batch, list) else [batch]

    for raw in items:
        raw_text = raw.decode() if isinstance(raw, bytes) else str(raw)
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            TRACE_WORKER_PROCESSED.labels(result="error").inc()
            logger.warning("trace_worker_invalid_json")
            continue

        try:
            async with factory() as session:
                await persist_trace_payload(session, payload)
                await session.commit()
            TRACE_WORKER_PROCESSED.labels(result="success").inc()
            processed += 1
        except Exception:
            TRACE_WORKER_PROCESSED.labels(result="error").inc()
            logger.exception("trace_worker_persist_failed")
            dlq_key = f"{settings.trace_queue_key}:dlq"
            await redis.lpush(dlq_key, raw_text)
            TRACE_DLQ_TOTAL.inc()

    return processed


async def run_forever() -> None:
    logger.info("trace_worker_started")
    try:
        while True:
            count = await process_queue_once()
            if count == 0:
                await asyncio.sleep(0.1)
    finally:
        await RedisClient.close()
        await dispose_engine()


def main() -> None:
    from tracelens.logging_setup import setup_logging

    setup_logging()
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
