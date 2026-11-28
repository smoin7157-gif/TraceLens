import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.db.models.alert import Alert
from tracelens.db.models.experiment import Experiment
from tracelens.db.models.evaluator import Evaluator
from tracelens.db.models.prompt import Prompt
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.observe.alerts import create_alert, fire_alert
from tracelens.observe.datasets import create_dataset, import_from_request_logs
from tracelens.observe.eval_queue import enqueue_eval_job
from tracelens.observe.experiments import create_experiment, run_experiment
from tracelens.observe.prompts import (
    add_prompt_version,
    compare_prompt_versions,
    create_prompt,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class PromptCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    slug: str = Field(min_length=1, max_length=64)


class PromptVersionRequest(BaseModel):
    template: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class DatasetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""


class DatasetImportRequest(BaseModel):
    request_log_ids: list[uuid.UUID] = Field(min_length=1)


class ExperimentCreateRequest(BaseModel):
    dataset_id: uuid.UUID
    name: str = Field(min_length=1, max_length=128)
    config: dict[str, object] = Field(default_factory=dict)


class EvaluatorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    kind: str = Field(pattern="^(regex|json_schema)$")
    config: dict[str, object] = Field(default_factory=dict)


class EvalEnqueueRequest(BaseModel):
    target_id: str
    output_text: str
    model: str | None = None
    experiment_id: uuid.UUID | None = None
    prompt_version_id: uuid.UUID | None = None


class AlertCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    metric: str = Field(min_length=1, max_length=64)
    threshold: float
    webhook_url: str = Field(min_length=1, max_length=512)


class AlertTestRequest(BaseModel):
    observed_value: float


async def _require_tenant(session: SessionDep, tenant_id: uuid.UUID) -> None:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.post("/tenants/{tenant_id}/prompts", status_code=status.HTTP_201_CREATED)
async def admin_create_prompt(
    tenant_id: uuid.UUID,
    body: PromptCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, str]:
    await _require_tenant(session, tenant_id)
    prompt = await create_prompt(session, tenant_id, name=body.name, slug=body.slug)
    return {"id": str(prompt.id), "slug": prompt.slug}


@router.post(
    "/tenants/{tenant_id}/prompts/{prompt_id}/versions",
    status_code=status.HTTP_201_CREATED,
)
async def admin_add_prompt_version(
    tenant_id: uuid.UUID,
    prompt_id: uuid.UUID,
    body: PromptVersionRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, int | str]:
    await _require_tenant(session, tenant_id)
    prompt = await session.get(Prompt, prompt_id)
    if prompt is None or prompt.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Prompt not found")
    version = await add_prompt_version(
        session,
        tenant_id,
        prompt_id=prompt_id,
        template=body.template,
        metadata=body.metadata,
    )
    return {"id": str(version.id), "version": version.version}


@router.get("/tenants/{tenant_id}/prompts/{prompt_id}/compare")
async def admin_compare_prompts(
    tenant_id: uuid.UUID,
    prompt_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, object]:
    await _require_tenant(session, tenant_id)
    rows = await compare_prompt_versions(session, tenant_id, prompt_id)
    return {"object": "prompt_compare", "versions": rows}


@router.post("/tenants/{tenant_id}/datasets", status_code=status.HTTP_201_CREATED)
async def admin_create_dataset(
    tenant_id: uuid.UUID,
    body: DatasetCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, str]:
    await _require_tenant(session, tenant_id)
    ds = await create_dataset(
        session,
        tenant_id,
        name=body.name,
        description=body.description,
    )
    return {"id": str(ds.id)}


@router.post("/tenants/{tenant_id}/datasets/{dataset_id}/import-requests")
async def admin_import_dataset_items(
    tenant_id: uuid.UUID,
    dataset_id: uuid.UUID,
    body: DatasetImportRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, int]:
    await _require_tenant(session, tenant_id)
    count = await import_from_request_logs(session, tenant_id, dataset_id, body.request_log_ids)
    return {"imported": count}


@router.post("/tenants/{tenant_id}/experiments", status_code=status.HTTP_201_CREATED)
async def admin_create_experiment(
    tenant_id: uuid.UUID,
    body: ExperimentCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, str]:
    await _require_tenant(session, tenant_id)
    exp = await create_experiment(
        session,
        tenant_id,
        dataset_id=body.dataset_id,
        name=body.name,
        config=body.config,
    )
    return {"id": str(exp.id), "status": exp.status}


@router.get("/tenants/{tenant_id}/experiments/{experiment_id}")
async def admin_get_experiment(
    tenant_id: uuid.UUID,
    experiment_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, object]:
    await _require_tenant(session, tenant_id)
    exp = await session.get(Experiment, experiment_id)
    if exp is None or exp.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "id": str(exp.id),
        "name": exp.name,
        "status": exp.status,
        "dataset_id": str(exp.dataset_id),
        "config": exp.config,
        "results": exp.results,
    }


@router.post("/tenants/{tenant_id}/experiments/{experiment_id}/run")
async def admin_run_experiment(
    tenant_id: uuid.UUID,
    experiment_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, object]:
    await _require_tenant(session, tenant_id)
    try:
        exp = await run_experiment(session, tenant_id, experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": str(exp.id), "status": exp.status, "results": exp.results}


@router.post("/tenants/{tenant_id}/evaluators", status_code=status.HTTP_201_CREATED)
async def admin_create_evaluator(
    tenant_id: uuid.UUID,
    body: EvaluatorCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, str]:
    await _require_tenant(session, tenant_id)
    entity = Evaluator(
        tenant_id=tenant_id,
        name=body.name,
        kind=body.kind,
        config=body.config,
    )
    session.add(entity)
    await session.flush()
    return {"id": str(entity.id), "kind": entity.kind}


@router.post("/tenants/{tenant_id}/evaluators/{evaluator_id}/enqueue")
async def admin_enqueue_eval(
    tenant_id: uuid.UUID,
    evaluator_id: uuid.UUID,
    body: EvalEnqueueRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, str]:
    await _require_tenant(session, tenant_id)
    evaluator = await session.get(Evaluator, evaluator_id)
    if evaluator is None or evaluator.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Evaluator not found")
    await enqueue_eval_job(
        tenant_id=tenant_id,
        evaluator_id=evaluator_id,
        target_id=body.target_id,
        output_text=body.output_text,
        model=body.model,
        experiment_id=body.experiment_id,
        prompt_version_id=body.prompt_version_id,
    )
    return {"status": "enqueued"}


@router.post("/tenants/{tenant_id}/alerts", status_code=status.HTTP_201_CREATED)
async def admin_create_alert(
    tenant_id: uuid.UUID,
    body: AlertCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, str]:
    await _require_tenant(session, tenant_id)
    try:
        alert = await create_alert(
            session,
            tenant_id,
            name=body.name,
            metric=body.metric,
            threshold=body.threshold,
            webhook_url=body.webhook_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": str(alert.id)}


@router.post("/tenants/{tenant_id}/alerts/{alert_id}/test")
async def admin_test_alert(
    tenant_id: uuid.UUID,
    alert_id: uuid.UUID,
    body: AlertTestRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> dict[str, str]:
    await _require_tenant(session, tenant_id)
    alert = await session.get(Alert, alert_id)
    if alert is None or alert.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    if body.observed_value < alert.threshold:
        return {"status": "below_threshold"}
    event = await fire_alert(session, alert, observed_value=body.observed_value)
    return {"status": "fired", "event_id": str(event.id)}
