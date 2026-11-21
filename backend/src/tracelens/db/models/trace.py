import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tracelens.db.base import Base, PrimaryKeyMixin, TimestampMixin


class Trace(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "traces"
    __table_args__ = (UniqueConstraint("tenant_id", "trace_id", name="uq_traces_tenant_trace_id"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tags: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="development")

    spans: Mapped[list["Span"]] = relationship(back_populates="trace", cascade="all, delete-orphan")


class Span(Base, PrimaryKeyMixin):
    __tablename__ = "spans"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("traces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_span_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spans.id", ondelete="SET NULL"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    attrs: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    trace: Mapped[Trace] = relationship(back_populates="spans")
