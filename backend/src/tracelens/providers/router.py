from tracelens.gateway.errors import GatewayValidationError

ProviderKind = str


def resolve_provider_for_model(model: str) -> ProviderKind:
    lowered = model.lower()
    if lowered.startswith("mock-"):
        return "mock"
    if lowered.startswith("claude"):
        return "anthropic"
    if lowered.startswith("gemini"):
        return "gemini"
    if lowered.startswith(("gpt-", "o1", "o3", "o4", "chatgpt")):
        return "openai"
    raise GatewayValidationError(
        f"The model `{model}` does not exist or you do not have access to it.",
        code="model_not_found",
    )
