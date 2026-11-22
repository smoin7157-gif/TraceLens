import os
from functools import lru_cache

from tracelens.embeddings.backends.minilm import (
    BagOfWordsEmbeddingBackend,
    HashEmbeddingBackend,
    SentenceTransformerBackend,
)


@lru_cache
def get_embedding_backend() -> (
    HashEmbeddingBackend | BagOfWordsEmbeddingBackend | SentenceTransformerBackend
):
    if os.environ.get("TRACELENS_USE_MINILM", "").lower() in {"1", "true", "yes"}:
        return SentenceTransformerBackend()
    if os.environ.get("TRACELENS_SEMANTIC_BAG_EMBED", "1").lower() in {"1", "true", "yes"}:
        return BagOfWordsEmbeddingBackend()
    return HashEmbeddingBackend()
