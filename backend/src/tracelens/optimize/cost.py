from decimal import Decimal

from tracelens.pipeline.context import GatewayContext

# USD per 1k tokens (skeleton list; extended in later phases)
MODEL_USD_PER_1K: dict[str, Decimal] = {
    "mock-gpt": Decimal("0.001"),
    "mock-gpt-4": Decimal("0.010"),
    "gpt-4o-mini": Decimal("0.015"),
}


def model_unit_price(model: str) -> Decimal:
    if model.startswith("mock-"):
        return MODEL_USD_PER_1K.get(model, Decimal("0.001"))
    return MODEL_USD_PER_1K.get(model, Decimal("0.020"))


def estimate_token_cost(model: str, tokens: int) -> Decimal:
    if tokens <= 0:
        return Decimal("0")
    price = model_unit_price(model)
    return (price * Decimal(tokens)) / Decimal(1000)


def compute_economics(context: GatewayContext) -> tuple[Decimal, Decimal]:
    """Return (cost_actual, cost_without_optimization) for this request."""
    requested = context.requested_model or (
        context.chat_request.model if context.chat_request else ""
    )
    selected = context.selected_model or requested
    tokens_in_orig = context.tokens_in_original
    if tokens_in_orig == 0 and context.chat_request is not None:
        tokens_in_orig = sum(max(1, len(m.content.split())) for m in context.chat_request.messages)
    tokens_in_final = context.tokens_in_final or tokens_in_orig
    tokens_out = context.tokens_out

    if context.chat_response is not None:
        tokens_out = context.chat_response.usage.completion_tokens
    elif tokens_out == 0 and context.cache_hit:
        tokens_out = max(1, tokens_in_final // 2)

    cost_without = estimate_token_cost(requested, tokens_in_orig + tokens_out)

    if context.cache_hit:
        cost_actual = Decimal("0")
    else:
        cost_actual = estimate_token_cost(selected, tokens_in_final + tokens_out)

    return cost_actual, cost_without
