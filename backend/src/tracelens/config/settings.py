from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from tracelens.config.budget import BudgetPolicy
from tracelens.config.pipeline import PipelineToggles, default_pipeline_toggles
from tracelens.config.resilience import CircuitBreakerPolicy, RetryPolicy, RoutingPolicy
from tracelens.config.security import (
    InjectionAction,
    PiiMode,
    RateLimitPolicy,
    SecurityPolicy,
    ValidationPolicy,
)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    database_url: str = Field(
        default="postgresql+asyncpg://tracelens:tracelens@localhost:5432/tracelens",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    admin_api_token: str = Field(default="", alias="ADMIN_API_TOKEN")
    mock_default_latency_ms: float = Field(default=5.0, alias="MOCK_DEFAULT_LATENCY_MS")
    mock_default_error_rate: float = Field(default=0.0, alias="MOCK_DEFAULT_ERROR_RATE")
    pipeline: PipelineToggles = Field(default_factory=default_pipeline_toggles)
    master_encryption_key: str = Field(default="", alias="MASTER_ENCRYPTION_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com/v1", alias="ANTHROPIC_BASE_URL"
    )
    google_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        alias="GOOGLE_BASE_URL",
    )
    rate_limit: RateLimitPolicy = Field(default_factory=RateLimitPolicy)
    validation: ValidationPolicy = Field(default_factory=ValidationPolicy)
    security_policy: SecurityPolicy = Field(default_factory=SecurityPolicy)
    pii_mode: PiiMode = Field(default="block", alias="PII_MODE")
    injection_action: InjectionAction = Field(default="block", alias="INJECTION_ACTION")
    circuit_breaker: CircuitBreakerPolicy = Field(default_factory=CircuitBreakerPolicy)
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    routing: RoutingPolicy = Field(default_factory=RoutingPolicy)
    budget: BudgetPolicy = Field(default_factory=BudgetPolicy)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
