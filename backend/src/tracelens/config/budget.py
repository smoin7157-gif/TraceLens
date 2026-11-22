from pydantic import BaseModel, Field


class BudgetPolicy(BaseModel):
    """Budget warnings and Redis counter behavior."""

    warn_fraction: float = Field(default=0.8, ge=0.0, le=1.0)
    warn_dedupe_seconds: int = Field(default=3600, ge=60)
