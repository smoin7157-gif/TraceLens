from decimal import Decimal

from tracelens.optimize.cost import compute_economics, estimate_token_cost
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    CompletionUsage,
)


def test_savings_reproducible_from_request_log_fields() -> None:
    context = GatewayContext(
        requested_model="mock-gpt-4",
        selected_model="mock-gpt",
        tokens_in_original=100,
        tokens_in_final=60,
        tokens_out=20,
        cache_hit=False,
        chat_request=ChatCompletionRequest(
            model="mock-gpt-4",
            messages=[ChatMessage(role="user", content="x" * 50)],
        ),
        chat_response=ChatCompletionResponse(
            id="id",
            created=1,
            model="mock-gpt",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="y"),
                )
            ],
            usage=CompletionUsage(prompt_tokens=60, completion_tokens=20, total_tokens=80),
        ),
    )
    actual, without = compute_economics(context)
    savings = without - actual
    expected_without = estimate_token_cost("mock-gpt-4", 120)
    expected_actual = estimate_token_cost("mock-gpt", 80)
    assert actual == expected_actual
    assert without == expected_without
    assert savings == expected_without - expected_actual
    assert savings > Decimal("0")


def test_cache_hit_zeroes_actual_cost() -> None:
    context = GatewayContext(
        requested_model="mock-gpt",
        selected_model="mock-gpt",
        tokens_in_original=40,
        tokens_in_final=40,
        tokens_out=10,
        cache_hit=True,
    )
    actual, without = compute_economics(context)
    assert actual == Decimal("0")
    assert without > Decimal("0")
