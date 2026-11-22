import uuid

import pytest

from tracelens.db.models.dataset import DatasetItem
from tracelens.observe.datasets import create_dataset
from tracelens.observe.experiments import create_experiment, run_experiment
from tracelens.observe.prompts import add_prompt_version, create_prompt


@pytest.mark.integration
@pytest.mark.asyncio
async def test_experiment_side_by_side_results(db_session) -> None:
    from tracelens.db.models.tenant import Tenant

    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Exp", slug=f"ex-{tenant_id.hex[:6]}")
    db_session.add(tenant)
    await db_session.flush()

    prompt = await create_prompt(db_session, tenant_id, name="Greeter", slug="greeter")
    v1 = await add_prompt_version(
        db_session,
        tenant_id,
        prompt_id=prompt.id,
        template="Say hi to {{model}}",
    )
    v2 = await add_prompt_version(
        db_session,
        tenant_id,
        prompt_id=prompt.id,
        template="Greet {{model}} politely",
    )
    ds = await create_dataset(db_session, tenant_id, name="smoke")
    db_session.add(
        DatasetItem(
            tenant_id=tenant_id,
            dataset_id=ds.id,
            input={"model": "mock-gpt"},
            expected_output="mock-gpt",
        )
    )
    await db_session.flush()

    exp = await create_experiment(
        db_session,
        tenant_id,
        dataset_id=ds.id,
        name="prompt-compare",
        config={
            "variants": [
                {"prompt_version_id": str(v1.id), "model": "mock-gpt"},
                {"prompt_version_id": str(v2.id), "model": "mock-gpt"},
            ]
        },
    )
    finished = await run_experiment(db_session, tenant_id, exp.id)
    assert finished.status == "completed"
    items = finished.results["items"]
    assert len(items) == 1
    assert len(items[0]["variants"]) == 2
