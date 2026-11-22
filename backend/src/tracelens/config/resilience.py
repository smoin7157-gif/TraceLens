from pydantic import BaseModel, Field


class CircuitBreakerPolicy(BaseModel):
    failure_threshold: int = Field(default=5, ge=1)
    failure_window_seconds: int = Field(default=60, ge=1)
    open_seconds: int = Field(default=30, ge=1)


class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=3, ge=1)
    base_delay_seconds: float = Field(default=0.25, ge=0.0)
    max_delay_seconds: float = Field(default=8.0, ge=0.0)


class RoutingPolicy(BaseModel):
    """Static fallback chains (hot-reload YAML in phase 14)."""

    fallback_chains: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "mock-gpt": ["mock-gpt", "mock-gpt-4"],
            "mock-gpt-4": ["mock-gpt-4", "mock-gpt"],
            "gpt-4o-mini": ["gpt-4o-mini", "mock-gpt"],
        }
    )
    weight_latency: float = 0.4
    weight_error: float = 0.4
    weight_cost: float = 0.1
    weight_quality: float = 0.1
