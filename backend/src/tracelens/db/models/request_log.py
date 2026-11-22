import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from tracelens.db.base import Base, PrimaryKeyMixin, TimestampMixin


class RequestLog(Base, PrimaryKeyMixin, TimestampMixin):
    """Per-gateway-call economics row (skeleton until phase-10 optimizations)."""

    __tablename__ = "requests_log"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    selected_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="completed")
    tokens_in_original: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    tokens_in_final: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    cost_actual: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, server_default="0")
    cost_without_optimization: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, server_default="0"
    )
    cache_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="miss")
    optimizations_applied: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    routing_explanation: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
