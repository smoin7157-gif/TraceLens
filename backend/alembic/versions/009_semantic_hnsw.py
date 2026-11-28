"""HNSW index and dedupe constraint for semantic cache.

Revision ID: 009
Revises: 008
"""

from collections.abc import Sequence

from alembic import op

revision: str = "009"
down_revision: str | Sequence[str] | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_semantic_cache_embedding_hnsw
        ON semantic_cache_index
        USING hnsw (embedding vector_cosine_ops)
        """
    )
    op.create_index(
        "uq_semantic_cache_tenant_model_hash",
        "semantic_cache_index",
        ["tenant_id", "model", "request_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_semantic_cache_tenant_model_hash", table_name="semantic_cache_index")
    op.execute("DROP INDEX IF EXISTS ix_semantic_cache_embedding_hnsw")