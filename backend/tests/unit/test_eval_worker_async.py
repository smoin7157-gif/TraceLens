import uuid
from unittest.mock import patch

import pytest
from fakeredis.aioredis import FakeRedis

from tracelens.db.models.evaluator import Evaluator
from tracelens.db.models.tenant import Tenant
from tracelens.db.redis_client import RedisClient
from tracelens.observe.eval_queue import enqueue_eval_job
from tracelens.workers.eval_worker import process_eval_queue_once


@pytest.mark.integration
@pytest.mark.asyncio
async def test_eval_worker_updates_quality_score(db_session) -> None:
    tenant_id = uuid.uuid4()
    db_session.add(Tenant(id=tenant_id, name="Eval", slug=f"ev-{tenant_id.hex[:6]}"))
    await db_session.flush()
    evaluator = Evaluator(
        tenant_id=tenant_id,
        name="regex-pass",
        kind="regex",
        config={"pattern": "ok"},
    )
    db_session.add(evaluator)
    await db_session.commit()

    fake = FakeRedis()
    with patch.object(RedisClient, "connection", return_value=fake):
        await enqueue_eval_job(
            tenant_id=tenant_id,
            evaluator_id=evaluator.id,
            target_id="case-1",
            output_text="all ok here",
            model="mock-gpt",
        )
        processed = await process_eval_queue_once()

    assert processed == 1
    score = await fake.get(f"tl:quality:{tenant_id}:mock-gpt")
    assert score is not None
    assert float(score) == 1.0
