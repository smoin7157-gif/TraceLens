import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.db.models.alert import Alert
from tracelens.db.models.experiment import Experiment
from tracelens.db.models.prompt import Prompt, PromptVersion
from tracelens.db.models.request_log import RequestLog
from tracelens.db.models.trace import Span, Trace
from tracelens.db.repositories.api_key import ApiKeyRepository
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.gateway.health import provider_health
from tracelens.observe.economics_agg import tenant_economics_summary, tenant_security_summary
from tracelens.observe.live_metrics import snapshot, snapshot_json
from tracelens.observe.prompts import compare_prompts_for_tenant
from tracelens.security.keys import issue_api_key

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def _require_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.get("/live")
async def dashboard_live(
    interval_seconds: float = Query(default=1.0, ge=0.25, le=5.0),
) -> StreamingResponse:
    async def generator() -> AsyncIterator[str]:
        while True:
            yield f"data: {snapshot_json()}\n\n"
            await asyncio.sleep(interval_seconds)

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/overview")
async def dashboard_overview(
    tenant_id: uuid.UUID,
    session: SessionDep,
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    live = snapshot()
    economics = await tenant_economics_summary(session, tenant_id)
    return {
        "tenant_id": str(tenant_id),
        "live": live,
        "economics": economics,
    }


@router.get("/providers")
async def dashboard_providers() -> dict[str, Any]:
    return await provider_health()


@router.get("/cost/recent")
async def dashboard_recent_cost(
    tenant_id: uuid.UUID,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    stmt = (
        select(RequestLog)
        .where(RequestLog.tenant_id == tenant_id)
        .options(
            load_only(
                RequestLog.request_id,
                RequestLog.model,
                RequestLog.cache_status,
                RequestLog.cost_actual,
                RequestLog.cost_without_optimization,
                RequestLog.created_at,
            )
        )
        .order_by(RequestLog.created_at.desc())
        .limit(limit)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return {
        "data": [
            {
                "request_id": row.request_id,
                "model": row.model,
                "cache_status": row.cache_status,
                "cost_actual": str(row.cost_actual),
                "cost_without_optimization": str(row.cost_without_optimization),
                "savings_usd": str(row.cost_without_optimization - row.cost_actual),
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.get("/traces")
async def dashboard_list_traces(
    tenant_id: uuid.UUID,
    session: SessionDep,
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    stmt = (
        select(Trace)
        .where(Trace.tenant_id == tenant_id)
        .options(
            load_only(
                Trace.trace_id,
                Trace.environment,
                Trace.tags,
                Trace.created_at,
            )
        )
        .order_by(Trace.created_at.desc())
        .limit(limit)
    )
    traces = list((await session.execute(stmt)).scalars().all())
    return {
        "data": [
            {
                "trace_id": trace.trace_id,
                "environment": trace.environment,
                "tags": trace.tags,
                "created_at": trace.created_at.isoformat(),
            }
            for trace in traces
        ]
    }


def _span_node(span: Span, children_map: dict[uuid.UUID, list[Span]]) -> dict[str, Any]:
    return {
        "id": str(span.id),
        "name": span.name,
        "kind": span.kind,
        "attrs": span.attrs,
        "started_at": span.started_at.isoformat(),
        "ended_at": span.ended_at.isoformat() if span.ended_at else None,
        "children": [_span_node(child, children_map) for child in children_map.get(span.id, [])],
    }


def _build_span_tree(spans: list[Span]) -> list[dict[str, Any]]:
    children_map: dict[uuid.UUID, list[Span]] = {}
    for span in spans:
        if span.parent_span_id is not None:
            children_map.setdefault(span.parent_span_id, []).append(span)
    roots = [span for span in spans if span.parent_span_id is None]
    if not roots and spans:
        known_parents = {span.parent_span_id for span in spans if span.parent_span_id}
        roots = [span for span in spans if span.id not in known_parents]
    return [_span_node(root, children_map) for root in roots]


@router.get("/traces/{trace_id}/tree")
async def dashboard_trace_tree(
    tenant_id: uuid.UUID,
    trace_id: str,
    session: SessionDep,
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    trace_stmt = select(Trace).where(Trace.tenant_id == tenant_id, Trace.trace_id == trace_id)
    trace = (await session.execute(trace_stmt)).scalar_one_or_none()
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    spans_stmt = select(Span).where(Span.tenant_id == tenant_id, Span.trace_id == trace.id)
    spans = list((await session.execute(spans_stmt)).scalars().all())
    return {
        "trace_id": trace.trace_id,
        "tree": _build_span_tree(spans),
        "span_count": len(spans),
    }


@router.get("/prompts")
async def dashboard_prompts(
    tenant_id: uuid.UUID,
    session: SessionDep,
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    return {"data": await compare_prompts_for_tenant(session, tenant_id)}


@router.get("/datasets/experiments")
async def dashboard_datasets_experiments(
    tenant_id: uuid.UUID,
    session: SessionDep,
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    experiments_stmt = select(Experiment).where(Experiment.tenant_id == tenant_id).limit(50)
    experiments = list((await session.execute(experiments_stmt)).scalars().all())
    return {
        "experiments": [
            {
                "id": str(exp.id),
                "name": exp.name,
                "status": exp.status,
                "dataset_id": str(exp.dataset_id),
                "created_at": exp.created_at.isoformat(),
            }
            for exp in experiments
        ]
    }


@router.get("/alerts")
async def dashboard_alerts(
    tenant_id: uuid.UUID,
    session: SessionDep,
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    stmt = select(Alert).where(Alert.tenant_id == tenant_id)
    alerts = list((await session.execute(stmt)).scalars().all())
    return {
        "data": [
            {
                "id": str(alert.id),
                "name": alert.name,
                "metric": alert.metric,
                "threshold": alert.threshold,
                "webhook_url": alert.webhook_url,
            }
            for alert in alerts
        ]
    }


@router.get("/security/summary")
async def dashboard_security_summary(
    tenant_id: uuid.UUID,
    session: SessionDep,
) -> dict[str, Any]:
    await _require_tenant(session, tenant_id)
    return await tenant_security_summary(session, tenant_id)


@router.post("/demo/seed")
async def dashboard_demo_seed(
    session: SessionDep,
    _admin: AdminDep,
    x_demo_slug: str | None = Header(default=None, alias="X-Demo-Slug"),
) -> dict[str, str]:
    slug = x_demo_slug or f"demo-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    tenant = await TenantRepository(session).create(name="Dashboard Demo", slug=slug)
    material = issue_api_key()
    await ApiKeyRepository(session, tenant.id).create(
        key_hash=material.key_hash,
        key_prefix=material.key_prefix,
        name="dashboard-demo",
        scopes=["gateway"],
        allowed_models=["mock-gpt", "mock-gpt-4"],
    )
    prompt = Prompt(tenant_id=tenant.id, name="Demo Prompt", slug="demo-prompt")
    session.add(prompt)
    await session.flush()
    session.add(
        PromptVersion(
            tenant_id=tenant.id,
            prompt_id=prompt.id,
            version=1,
            template="Answer about {{model}}",
        )
    )
    return {
        "tenant_id": str(tenant.id),
        "slug": slug,
        "api_key_secret": material.raw_key,
    }
