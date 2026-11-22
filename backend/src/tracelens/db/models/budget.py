import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from tracelens.db.base import Base, PrimaryKeyMixin, TimestampMixin


class Budget(Base, PrimaryKeyMixin, TimestampMixin):
    """Spend caps for API keys (optional daily/monthly token and USD limits)."""

    __tablename__ = "budgets"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    daily_tokens: Mapped[int | None] = mapped_column(nullable=True)
    monthly_tokens: Mapped[int | None] = mapped_column(nullable=True)
    daily_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    monthly_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
