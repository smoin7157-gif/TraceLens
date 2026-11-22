import pytest

from tracelens.gateway.errors import GatewayValidationError
from tracelens.providers.router import resolve_provider_for_model


def test_resolve_provider_routes_models() -> None:
    assert resolve_provider_for_model("mock-gpt") == "mock"
    assert resolve_provider_for_model("gpt-4o-mini") == "openai"
    assert resolve_provider_for_model("claude-3-5-sonnet-latest") == "anthropic"
    assert resolve_provider_for_model("gemini-2.0-flash") == "gemini"


def test_resolve_provider_unknown_model() -> None:
    with pytest.raises(GatewayValidationError):
        resolve_provider_for_model("unknown-model")
