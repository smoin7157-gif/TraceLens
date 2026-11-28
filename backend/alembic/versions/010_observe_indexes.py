"""Indexes for eval runs and prompt versions.

Revision ID: 010
Revises: 009
"""

from collections.abc import Sequence

from alembic import op

revision: str = "010"
down_revision: str | Sequence[str] | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_eval_runs_tenant_model",
        "eval_runs",
        ["tenant_id", "model"],
        unique=False,
    )
    op.create_index(
        "ix_prompt_versions_tenant_prompt",
        "prompt_versions",
        ["tenant_id", "prompt_id"],
        unique=False,
    )
    op.create_index(
        "ix_alert_events_tenant_created",
        "alert_events",
        ["tenant_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_alert_events_tenant_created", table_name="alert_events")
    op.drop_index("ix_prompt_versions_tenant_prompt", table_name="prompt_versions")
    op.drop_index("ix_eval_runs_tenant_model", table_name="eval_runs")