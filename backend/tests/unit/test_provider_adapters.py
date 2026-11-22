import pytest
import respx
from httpx import Response

from tracelens.providers.anthropic import AnthropicProvider
from tracelens.providers.gemini import GeminiProvider
from tracelens.providers.openai import OpenAIProvider
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


@pytest.mark.asyncio
@respx.mock
async def test_openai_adapter_maps_response() -> None:
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1_700_000_000,
                "model": "gpt-4o-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hello from openai"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            },
        )
    )
    provider = OpenAIProvider("sk-test")
    response = await provider.chat_completion(
        ChatCompletionRequest(
            model="gpt-4o-mini",
            messages=[ChatMessage(role="user", content="hi")],
        ),
        completion_id="chatcmpl-override",
    )
    assert response.id == "chatcmpl-override"
    assert response.choices[0].message.content == "hello from openai"


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_adapter_maps_response() -> None:
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(
            200,
            json={
                "id": "msg_123",
                "content": [{"type": "text", "text": "hello from anthropic"}],
                "usage": {"input_tokens": 4, "output_tokens": 6},
            },
        )
    )
    response = await AnthropicProvider("ant-test").chat_completion(
        ChatCompletionRequest(
            model="claude-3-5-sonnet-latest",
            messages=[ChatMessage(role="user", content="hi")],
        )
    )
    assert "anthropic" in response.choices[0].message.content


@pytest.mark.asyncio
@respx.mock
async def test_gemini_adapter_maps_response() -> None:
    respx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    ).mock(
        return_value=Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "hello from gemini"}]}}],
                "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 3},
            },
        )
    )
    response = await GeminiProvider("google-test").chat_completion(
        ChatCompletionRequest(
            model="gemini-2.0-flash",
            messages=[ChatMessage(role="user", content="hi")],
        )
    )
    assert response.choices[0].message.content == "hello from gemini"
