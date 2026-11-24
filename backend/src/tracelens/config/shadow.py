from pydantic import BaseModel, Field


class ShadowPolicy(BaseModel):
    """Fire-and-forget duplicate calls to a shadow model for drift checks."""

    enabled: bool = False
    sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    shadow_model: str = "mock-gpt-4"
