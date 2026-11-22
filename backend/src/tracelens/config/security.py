from typing import Literal

from pydantic import BaseModel, Field


class SecurityPolicy(BaseModel):
    """Fail-open vs fail-closed per feature (defaults match PLAN.md)."""

    rate_limit_on_redis_failure: Literal["open", "closed"] = "open"
    security_scan_on_redis_failure: Literal["open", "closed"] = "closed"


class RateLimitPolicy(BaseModel):
    per_key_per_minute: int = Field(default=60, ge=1)
    per_ip_per_minute: int = Field(default=120, ge=1)
    window_seconds: int = Field(default=60, ge=1)


class ValidationPolicy(BaseModel):
    max_request_bytes: int = Field(default=1_048_576, ge=1024)
    max_tokens_cap: int = Field(default=8192, ge=1)


PiiMode = Literal["block", "redact", "log_only"]
InjectionAction = Literal["block", "log"]
