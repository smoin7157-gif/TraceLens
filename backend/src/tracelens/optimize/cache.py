import hashlib
import json
import uuid

from redis.asyncio import Redis

from tracelens.config import get_settings
from tracelens.providers.schemas import ChatCompletionResponse


def cache_prompt_digest(messages: list[dict[str, str]], model: str) -> str:
    payload = json.dumps(
        {"model": model, "messages": messages},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


def exact_cache_key(tenant_id: uuid.UUID, model: str, digest: str) -> str:
    return f"tl:cache:exact:{tenant_id}:{model}:{digest}"


class ExactCache:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._ttl = get_settings().cache.exact_ttl_seconds

    async def get(
        self,
        tenant_id: uuid.UUID,
        model: str,
        digest: str,
    ) -> ChatCompletionResponse | None:
        raw = await self._redis.get(exact_cache_key(tenant_id, model, digest))
        if raw is None:
            return None
        data = json.loads(raw)
        return ChatCompletionResponse.model_validate(data)

    async def set(
        self,
        tenant_id: uuid.UUID,
        model: str,
        digest: str,
        response: ChatCompletionResponse,
    ) -> None:
        key = exact_cache_key(tenant_id, model, digest)
        payload = response.model_dump_json()
        await self._redis.set(key, payload, ex=self._ttl)
