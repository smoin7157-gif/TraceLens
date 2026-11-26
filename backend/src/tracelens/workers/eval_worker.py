import asyncio
import json
import logging
import uuid

from sqlalchemy import func, select

from tracelens.config import get_settings
from tracelens.db.models.evaluator import EvalRun, Evaluator
from tracelens.db.redis_client import RedisClient
from tracelens.db.session import async_session_factory, dispose_engine
from tracelens.observe.evaluators import evaluate_output
from tracelens.observe.prompts import refresh_prompt_version_metrics
from tracelens.observe.quality_scores import set_quality_score

logger = logging.getLogger(__name__)


async def process_eval_queue_once() -> int:
    settings = get_settings().observe
    redis = RedisClient.connection()
    factory = async_session_factory()
    processed = 0

    batch = await redis.rpop(settings.eval_queue_key, count=settings.worker_batch_size)
    if not batch:
        return 0
    items = batch if isinstance(batch, list) else [batch]

    for raw in items:
        raw_text = raw.decode() if isinstance(raw, bytes) else str(raw)
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        tenant_id = uuid.UUID(str(payload["tenant_id"]))
        evaluator_id = uuid.UUID(str(payload["evaluator_id"]))

        async with factory() as session:
            evaluator = await session.get(Evaluator, evaluator_id)
            if evaluator is None or evaluator.tenant_id != tenant_id:
                continue
            output_text = str(payload.get("output_text", ""))
            score, details = evaluate_output(evaluator.kind, evaluator.config, output_text)
            run = EvalRun(
                tenant_id=tenant_id,
                evaluator_id=evaluator_id,
                experiment_id=uuid.UUID(payload["experiment_id"])
                if payload.get("experiment_id")
                else None,
                target_id=str(payload.get("target_id", "")),
                status="completed",
                score=score,
                model=str(payload.get("model")) if payload.get("model") else None,
                output={
                    **details,
                    "prompt_version_id": payload.get("prompt_version_id"),
                },
            )
            session.add(run)
            await session.flush()

            model = run.model
            if model:
                stmt = select(func.avg(EvalRun.score)).where(
                    EvalRun.tenant_id == tenant_id,
                    EvalRun.model == model,
                    EvalRun.status == "completed",
                )
                avg = (await session.execute(stmt)).scalar_one()
                if avg is not None:
                    await set_quality_score(redis, tenant_id, model, float(avg))

            prompt_version_id = payload.get("prompt_version_id")
            if prompt_version_id:
                await refresh_prompt_version_metrics(
                    session,
                    tenant_id,
                    uuid.UUID(str(prompt_version_id)),
                )

            await session.commit()
            processed += 1

    return processed


async def run_forever() -> None:
    logger.info("eval_worker_started")
    try:
        while True:
            count = await process_eval_queue_once()
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
