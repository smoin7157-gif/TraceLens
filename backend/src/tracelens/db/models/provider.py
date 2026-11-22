from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from tracelens.db.base import Base, PrimaryKeyMixin, TimestampMixin


class Provider(Base, PrimaryKeyMixin, TimestampMixin):
    __tablename__ = "providers"

    provider_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
