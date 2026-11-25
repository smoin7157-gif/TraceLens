import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.evaluator import EvalRun
from tracelens.db.models.prompt import Prompt, PromptVersion


async def create_prompt(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str,
    slug: str,
) -> Prompt:
    entity = Prompt(tenant_id=tenant_id, name=name, slug=slug)
    session.add(entity)
    await session.flush()
    return entity


async def add_prompt_version(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    prompt_id: uuid.UUID,
    template: str,
    metadata: dict[str, object] | None = None,
) -> PromptVersion:
    stmt = select(func.coalesce(func.max(PromptVersion.version), 0)).where(
        PromptVersion.prompt_id == prompt_id,
        PromptVersion.tenant_id == tenant_id,
    )
    result = await session.execute(stmt)
    next_version = int(result.scalar_one()) + 1
    entity = PromptVersion(
        tenant_id=tenant_id,
        prompt_id=prompt_id,
        version=next_version,
        template=template,
        metadata_=metadata or {},
    )
    session.add(entity)
    await session.flush()
    return entity


def _version_metrics(
    versions: list[PromptVersion],
    eval_runs: list[EvalRun],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for version in versions:
        scores = [
            float(run.score)
            for run in eval_runs
            if run.score is not None and str(run.output.get("prompt_version_id")) == str(version.id)
        ]
        metrics = dict(version.metrics or {})
        if scores:
            metrics = {
                "mean_score": sum(scores) / len(scores),
                "eval_count": len(scores),
            }
        rows.append(
            {
                "prompt_version_id": str(version.id),
                "version": version.version,
                "metrics": metrics,
            }
        )
    return rows


async def compare_prompt_versions(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    prompt_id: uuid.UUID,
) -> list[dict[str, Any]]:
    versions_stmt = select(PromptVersion).where(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.prompt_id == prompt_id,
    )
    versions = list((await session.execute(versions_stmt)).scalars().all())
    runs_stmt = select(EvalRun).where(EvalRun.tenant_id == tenant_id)
    eval_runs = list((await session.execute(runs_stmt)).scalars().all())
    return _version_metrics(versions, eval_runs)


async def compare_prompts_for_tenant(
    session: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[dict[str, Any]]:
    prompts = list(
        (await session.execute(select(Prompt).where(Prompt.tenant_id == tenant_id))).scalars().all()
    )
    if not prompts:
        return []
    prompt_ids = [prompt.id for prompt in prompts]
    versions = list(
        (
            await session.execute(
                select(PromptVersion).where(
                    PromptVersion.tenant_id == tenant_id,
                    PromptVersion.prompt_id.in_(prompt_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    eval_runs = list(
        (await session.execute(select(EvalRun).where(EvalRun.tenant_id == tenant_id)))
        .scalars()
        .all()
    )
    versions_by_prompt: dict[uuid.UUID, list[PromptVersion]] = {}
    for version in versions:
        versions_by_prompt.setdefault(version.prompt_id, []).append(version)

    rows: list[dict[str, Any]] = []
    for prompt in prompts:
        prompt_versions = versions_by_prompt.get(prompt.id, [])
        rows.append(
            {
                "id": str(prompt.id),
                "name": prompt.name,
                "slug": prompt.slug,
                "versions": _version_metrics(prompt_versions, eval_runs),
            }
        )
    return rows


async def refresh_prompt_version_metrics(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    prompt_version_id: uuid.UUID,
) -> None:
    runs_stmt = select(EvalRun).where(EvalRun.tenant_id == tenant_id)
    eval_runs = list((await session.execute(runs_stmt)).scalars().all())
    scores = [
        float(run.score)
        for run in eval_runs
        if run.score is not None
        and str(run.output.get("prompt_version_id")) == str(prompt_version_id)
    ]
    version = await session.get(PromptVersion, prompt_version_id)
    if version is None or version.tenant_id != tenant_id:
        return
    version.metrics = {
        "mean_score": (sum(scores) / len(scores)) if scores else 0.0,
        "eval_count": len(scores),
    }
    await session.flush()
