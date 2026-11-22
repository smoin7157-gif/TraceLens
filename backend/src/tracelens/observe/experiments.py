import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.dataset import DatasetItem
from tracelens.db.models.experiment import Experiment
from tracelens.db.models.prompt import PromptVersion


def render_prompt_template(template: str, item_input: dict[str, object]) -> str:
    text = template
    for key, value in item_input.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


async def create_experiment(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    dataset_id: uuid.UUID,
    name: str,
    config: dict[str, object],
) -> Experiment:
    entity = Experiment(
        tenant_id=tenant_id,
        dataset_id=dataset_id,
        name=name,
        config=config,
        status="pending",
    )
    session.add(entity)
    await session.flush()
    return entity


async def run_experiment(
    session: AsyncSession, tenant_id: uuid.UUID, experiment_id: uuid.UUID
) -> Experiment:
    experiment = await session.get(Experiment, experiment_id)
    if experiment is None or experiment.tenant_id != tenant_id:
        msg = "Experiment not found"
        raise ValueError(msg)

    items_stmt = select(DatasetItem).where(
        DatasetItem.tenant_id == tenant_id,
        DatasetItem.dataset_id == experiment.dataset_id,
    )
    items = list((await session.execute(items_stmt)).scalars().all())
    raw_variants = experiment.config.get("variants", [])
    variants = list(raw_variants) if isinstance(raw_variants, list) else []
    side_by_side: list[dict[str, object]] = []

    for item in items:
        variant_rows: list[dict[str, object]] = []
        row: dict[str, object] = {"dataset_item_id": str(item.id), "variants": variant_rows}
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            prompt_version_id = uuid.UUID(str(variant["prompt_version_id"]))
            version = await session.get(PromptVersion, prompt_version_id)
            if version is None:
                continue
            rendered = render_prompt_template(version.template, item.input)
            expected = item.expected_output or ""
            score = 1.0 if expected and expected in rendered else 0.5
            variant_rows.append(
                {
                    "prompt_version_id": str(prompt_version_id),
                    "model": variant.get("model"),
                    "rendered_preview": rendered[:200],
                    "score": score,
                }
            )
        side_by_side.append(row)

    experiment.status = "completed"
    experiment.results = {"items": side_by_side}
    await session.flush()
    return experiment
