import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from tracelens.api.deps import AdminDep, SessionDep
from tracelens.db.repositories.api_key import ApiKeyRepository
from tracelens.db.repositories.budget import BudgetRepository
from tracelens.db.repositories.tenant import TenantRepository
from tracelens.security.webhooks import UnsafeWebhookError, validate_webhook_url

router = APIRouter(prefix="/admin", tags=["admin"])


class BudgetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    daily_tokens: int | None = Field(default=None, ge=0)
    monthly_tokens: int | None = Field(default=None, ge=0)
    daily_usd: Decimal | None = Field(default=None, ge=0)
    monthly_usd: Decimal | None = Field(default=None, ge=0)
    webhook_url: str | None = Field(default=None, max_length=512)


class BudgetResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    daily_tokens: int | None
    monthly_tokens: int | None
    daily_usd: Decimal | None
    monthly_usd: Decimal | None
    webhook_url: str | None


class AttachBudgetRequest(BaseModel):
    budget_id: uuid.UUID


@router.post(
    "/tenants/{tenant_id}/budgets",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_budget(
    tenant_id: uuid.UUID,
    body: BudgetCreateRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> BudgetResponse:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    webhook_url = body.webhook_url
    if webhook_url:
        try:
            webhook_url = validate_webhook_url(webhook_url)
        except UnsafeWebhookError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    record = await BudgetRepository(session, tenant_id).create(
        name=body.name,
        daily_tokens=body.daily_tokens,
        monthly_tokens=body.monthly_tokens,
        daily_usd=body.daily_usd,
        monthly_usd=body.monthly_usd,
        webhook_url=webhook_url,
    )
    return BudgetResponse(
        id=record.id,
        tenant_id=record.tenant_id,
        name=record.name,
        daily_tokens=record.daily_tokens,
        monthly_tokens=record.monthly_tokens,
        daily_usd=record.daily_usd,
        monthly_usd=record.monthly_usd,
        webhook_url=record.webhook_url,
    )


@router.post(
    "/tenants/{tenant_id}/api-keys/{key_id}/budget", status_code=status.HTTP_204_NO_CONTENT
)
async def attach_budget_to_key(
    tenant_id: uuid.UUID,
    key_id: uuid.UUID,
    body: AttachBudgetRequest,
    _admin: AdminDep,
    session: SessionDep,
) -> None:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    budget = await BudgetRepository(session, tenant_id).get_by_id(body.budget_id)
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    key = await ApiKeyRepository(session, tenant_id).get_by_id(key_id)
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    key.budget_id = body.budget_id
    await session.flush()


@router.get("/tenants/{tenant_id}/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    tenant_id: uuid.UUID,
    _admin: AdminDep,
    session: SessionDep,
) -> list[BudgetResponse]:
    tenant = await TenantRepository(session).get_by_id(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    rows = await BudgetRepository(session, tenant_id).list_all()
    return [
        BudgetResponse(
            id=row.id,
            tenant_id=row.tenant_id,
            name=row.name,
            daily_tokens=row.daily_tokens,
            monthly_tokens=row.monthly_tokens,
            daily_usd=row.daily_usd,
            monthly_usd=row.monthly_usd,
            webhook_url=row.webhook_url,
        )
        for row in rows
    ]
