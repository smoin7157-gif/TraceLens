import asyncio
import hashlib
import math
import re
from collections.abc import Sequence

_EMBED_DIM = 384


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def _hash_dims(seed: bytes) -> list[float]:
    out: list[float] = []
    counter = 0
    while len(out) < _EMBED_DIM:
        digest = hashlib.sha256(seed + counter.to_bytes(2, "big")).digest()
        for i in range(0, len(digest) - 3, 4):
            value = int.from_bytes(digest[i : i + 4], "big", signed=True)
            out.append(float(value) / 2**31)
            if len(out) >= _EMBED_DIM:
                break
        counter += 1
    return _normalize(out)


class HashEmbeddingBackend:
    """Deterministic embeddings (default for CI/dev without torch)."""

    async def embed(self, text: str) -> list[float]:
        return _hash_dims(hashlib.sha256(text.encode("utf-8")).digest())

    async def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class BagOfWordsEmbeddingBackend:
    """Token-overlap friendly vectors for semantic near-dup tests."""

    async def embed(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return _hash_dims(b"empty")
        vec = [0.0] * _EMBED_DIM
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % _EMBED_DIM
            vec[index] += 1.0
        return _normalize(vec)

    async def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]


class SentenceTransformerBackend:
    """Optional all-MiniLM-L6-v2 backend (install sentence-transformers)."""

    def __init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            msg = "sentence-transformers not installed; use HashEmbeddingBackend"
            raise RuntimeError(msg) from exc
        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self._embed_sync, text)

    def _embed_sync(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return [float(x) for x in vector]

    async def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return await asyncio.to_thread(self._embed_batch_sync, list(texts))

    def _embed_batch_sync(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [[float(x) for x in row] for row in vectors]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))
