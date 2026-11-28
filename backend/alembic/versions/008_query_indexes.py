"""Composite indexes for dashboard and economics queries.

Revision ID: 008
Revises: 007
"""

from collections.abc import Sequence

from alembic import op

revision: str = "008"
down_revision: str | Sequence[str] | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_requests_log_tenant_created",
        "requests_log",
        ["tenant_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_traces_tenant_created",
        "traces",
        ["tenant_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_spans_tenant_trace",
        "spans",
        ["tenant_id", "trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_requests_log_tenant_status",
        "requests_log",
        ["tenant_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_requests_log_tenant_status", table_name="requests_log")
    op.drop_index("ix_spans_tenant_trace", table_name="spans")
    op.drop_index("ix_traces_tenant_created", table_name="traces")
    op.drop_index("ix_requests_log_tenant_created", table_name="requests_log")