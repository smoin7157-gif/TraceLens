from pydantic import BaseModel, Field


class CachePolicy(BaseModel):
    exact_ttl_seconds: int = Field(default=3600, ge=60)
    semantic_ttl_seconds: int = Field(default=86_400, ge=60)
    semantic_similarity_threshold: float = Field(default=0.92, ge=0.5, le=1.0)


class CompressPolicy(BaseModel):
    max_history_messages: int = Field(default=20, ge=2)
    collapse_whitespace: bool = True


class DowngradePolicy(BaseModel):
    """Safe model downgrade when complexity is low and eval score is sufficient."""

    complexity_word_threshold: int = Field(default=120, ge=1)
    min_eval_quality_score: float = Field(default=0.75, ge=0.0, le=1.0)
    stub_eval_quality_score: float = Field(default=0.85, ge=0.0, le=1.0)
