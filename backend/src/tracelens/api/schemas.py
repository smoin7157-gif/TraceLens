import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    scopes: list[str] = Field(default_factory=lambda: ["gateway"])
    allowed_models: list[str] = Field(default_factory=list)


class ApiKeyCreateResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    key_prefix: str
    secret: str
    scopes: list[str]
    allowed_models: list[str]
    created_at: datetime


class ApiKeyListItem(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    key_prefix: str
    scopes: list[str]
    allowed_models: list[str]
    created_at: datetime
    revoked_at: datetime | None
