import uuid
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from tracelens.db.base import Base
from tracelens.db.exceptions import TenantIsolationError


class TenantScopedRepository[ModelT: Base]:
    """Repository that always scopes reads and writes to a single tenant."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def _assert_tenant_owned(self, model: ModelT) -> None:
        tenant_id = getattr(model, "tenant_id", None)
        if tenant_id is not None and tenant_id != self.tenant_id:
            raise TenantIsolationError(
                f"{self.model.__name__} belongs to tenant {tenant_id}, not {self.tenant_id}"
            )

    def _scoped_select(self) -> Select[Any]:
        if not hasattr(self.model, "tenant_id"):
            msg = f"{self.model.__name__} is not tenant-scoped"
            raise TypeError(msg)
        return select(self.model).where(self.model.tenant_id == self.tenant_id)  # type: ignore[attr-defined]

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        stmt = self._scoped_select().where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return cast(ModelT | None, result.scalar_one_or_none())

    async def list_all(self, *, limit: int = 100) -> list[ModelT]:
        stmt = self._scoped_select().limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _prepare_create(self, data: dict[str, object]) -> dict[str, object]:
        if "tenant_id" in data and data["tenant_id"] != self.tenant_id:
            raise TenantIsolationError("Cannot create rows for another tenant")
        data = dict(data)
        data["tenant_id"] = self.tenant_id
        return data

    async def add(self, entity: ModelT) -> ModelT:
        self._assert_tenant_owned(entity)
        self.session.add(entity)
        await self.session.flush()
        return entity
