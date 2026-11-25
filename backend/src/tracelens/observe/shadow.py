import asyncio
import hashlib
import logging

from fastapi import Request

from tracelens.config import get_settings
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


def should_shadow(*, request_id: str | None, sample_rate: float) -> bool:
    if sample_rate <= 0.0:
        return False
    if sample_rate >= 1.0:
        return True
    if not request_id:
        return False
    digest = hashlib.sha256(request_id.encode("utf-8")).digest()
    bucket = digest[0] / 255.0
    return bucket < sample_rate


async def run_shadow_call(
    registry: ProviderRegistry,
    *,
    http_request: Request,
    context: GatewayContext,
) -> dict[str, object] | None:
    settings = get_settings()
    policy = settings.shadow
    if not policy.enabled or context.chat_request is None:
        return None
    if not should_shadow(request_id=context.request_id, sample_rate=policy.sample_rate):
        return None

    shadow_request = context.chat_request.model_copy(update={"model": policy.shadow_model})
    try:
        response = await registry.chat_completion(
            shadow_request,
            http_request=http_request,
            completion_id=f"{context.request_id}-shadow",
        )
        text = response.choices[0].message.content
        return {
            "shadow_model": policy.shadow_model,
            "shadow_text": text,
            "primary_model": context.selected_model,
        }
    except Exception as exc:
        logger.warning("shadow_call_failed", extra={"error": str(exc)})
        return {"shadow_model": policy.shadow_model, "error": str(exc)}


def schedule_shadow_call(
    registry: ProviderRegistry,
    *,
    http_request: Request,
    context: GatewayContext,
) -> None:
    settings = get_settings()
    if not settings.shadow.enabled:
        return
    if context.chat_request is None or context.chat_request.stream:
        return

    async def _worker() -> None:
        result = await run_shadow_call(registry, http_request=http_request, context=context)
        if result is not None:
            context.routing_explanation["shadow"] = result

    asyncio.create_task(_worker())


async def run_shadow_call_sync(
    registry: ProviderRegistry,
    *,
    http_request: Request,
    context: GatewayContext,
) -> dict[str, object] | None:
    """Test-friendly synchronous shadow execution."""
    result = await run_shadow_call(registry, http_request=http_request, context=context)
    if result is not None:
        context.routing_explanation["shadow"] = result
    return result
