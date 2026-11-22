import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.config import get_settings
from tracelens.db.models.semantic_cache import SemanticCacheEntry
from tracelens.embeddings import get_embedding_backend
from tracelens.embeddings.backends.minilm import cosine_similarity
from tracelens.providers.schemas import ChatCompletionResponse


def prompt_plaintext(messages: list[dict[str, str]]) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


class SemanticCache:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._backend = get_embedding_backend()
        self._settings = get_settings().cache

    async def lookup(
        self,
        tenant_id: uuid.UUID,
        model: str,
        messages: list[dict[str, str]],
    ) -> tuple[ChatCompletionResponse | None, float | None]:
        prompt = prompt_plaintext(messages)
        query_vec = await self._backend.embed(prompt)
        threshold = self._settings.semantic_similarity_threshold

        stmt = (
            select(SemanticCacheEntry)
            .where(
                SemanticCacheEntry.tenant_id == tenant_id,
                SemanticCacheEntry.model == model,
            )
            .order_by(SemanticCacheEntry.created_at.desc())
            .limit(25)
        )
        result = await self._session.execute(stmt)
        entries = list(result.scalars().all())
        now = datetime.now(UTC)
        best_score = -1.0
        best: SemanticCacheEntry | None = None
        for entry in entries:
            if entry.expires_at is not None and entry.expires_at < now:
                continue
            score = cosine_similarity(query_vec, entry.embedding)
            if score > best_score:
                best_score = score
                best = entry

        if best is None or best_score < threshold:
            return None, best_score if best_score >= 0 else None

        response = ChatCompletionResponse.model_validate(best.response_payload)
        return response, best_score

    async def store(
        self,
        tenant_id: uuid.UUID,
        model: str,
        messages: list[dict[str, str]],
        request_hash: str,
        response: ChatCompletionResponse,
    ) -> None:
        prompt = prompt_plaintext(messages)
        vector = await self._backend.embed(prompt)
        expires = datetime.now(UTC) + timedelta(seconds=self._settings.semantic_ttl_seconds)
        entry = SemanticCacheEntry(
            tenant_id=tenant_id,
            model=model,
            request_hash=request_hash,
            prompt_text=prompt[:4000],
            embedding=vector,
            response_payload=response.model_dump(),
            expires_at=expires,
        )
        self._session.add(entry)
        await self._session.flush()
