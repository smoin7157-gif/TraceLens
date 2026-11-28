import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

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

        now = datetime.now(UTC)
        not_expired = or_(
            SemanticCacheEntry.expires_at.is_(None),
            SemanticCacheEntry.expires_at > now,
        )
        distance = SemanticCacheEntry.embedding.cosine_distance(query_vec)
        stmt = (
            select(SemanticCacheEntry, distance.label("distance"))
            .where(
                SemanticCacheEntry.tenant_id == tenant_id,
                SemanticCacheEntry.model == model,
                not_expired,
            )
            .options(
                load_only(
                    SemanticCacheEntry.embedding,
                    SemanticCacheEntry.response_payload,
                    SemanticCacheEntry.expires_at,
                )
            )
            .order_by(distance)
            .limit(5)
        )
        result = await self._session.execute(stmt)
        rows = list(result.all())
        if not rows:
            return None, None
        best_entry, _ = rows[0]
        best_score = cosine_similarity(query_vec, best_entry.embedding)
        if best_score < threshold:
            return None, best_score
        response = ChatCompletionResponse.model_validate(best_entry.response_payload)
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
        payload = response.model_dump()
        stmt = (
            insert(SemanticCacheEntry)
            .values(
                tenant_id=tenant_id,
                model=model,
                request_hash=request_hash,
                prompt_text=prompt[:4000],
                embedding=vector,
                response_payload=payload,
                expires_at=expires,
            )
            .on_conflict_do_update(
                index_elements=["tenant_id", "model", "request_hash"],
                set_={
                    "prompt_text": prompt[:4000],
                    "embedding": vector,
                    "response_payload": payload,
                    "expires_at": expires,
                },
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
