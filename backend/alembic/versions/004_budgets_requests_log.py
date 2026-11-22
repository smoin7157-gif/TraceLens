"""Budgets table, api_keys.budget_id, requests_log economics.

Revision ID: 004
Revises: 003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("daily_tokens", sa.Integer(), nullable=True),
        sa.Column("monthly_tokens", sa.Integer(), nullable=True),
        sa.Column("daily_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("monthly_usd", sa.Numeric(12, 6), nullable=True),
        sa.Column("webhook_url", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_budgets_tenant_id", "budgets", ["tenant_id"])

    op.add_column(
        "api_keys",
        sa.Column("budget_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_api_keys_budget_id",
        "api_keys",
        "budgets",
        ["budget_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_api_keys_budget_id", "api_keys", ["budget_id"])

    op.create_table(
        "requests_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("selected_model", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="completed", nullable=False),
        sa.Column("tokens_in_original", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens_in_final", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens_out", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "cost_actual", sa.Numeric(12, 6), server_default="0", nullable=False
        ),
        sa.Column(
            "cost_without_optimization",
            sa.Numeric(12, 6),
            server_default="0",
            nullable=False,
        ),
        sa.Column("cache_status", sa.String(length=32), server_default="miss", nullable=False),
        sa.Column(
            "optimizations_applied",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "routing_explanation",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_requests_log_tenant_id", "requests_log", ["tenant_id"])
    op.create_index("ix_requests_log_api_key_id", "requests_log", ["api_key_id"])
    op.create_index("ix_requests_log_request_id", "requests_log", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_requests_log_request_id", table_name="requests_log")
    op.drop_index("ix_requests_log_api_key_id", table_name="requests_log")
    op.drop_index("ix_requests_log_tenant_id", table_name="requests_log")
    op.drop_table("requests_log")
    op.drop_index("ix_api_keys_budget_id", table_name="api_keys")
    op.drop_constraint("fk_api_keys_budget_id", "api_keys", type_="foreignkey")
    op.drop_column("api_keys", "budget_id")
    op.drop_index("ix_budgets_tenant_id", table_name="budgets")
    op.drop_table("budgets")