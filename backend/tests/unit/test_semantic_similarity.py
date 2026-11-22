import pytest

from tracelens.embeddings.backends.minilm import BagOfWordsEmbeddingBackend, cosine_similarity


@pytest.mark.asyncio
async def test_near_duplicate_prompts_meet_threshold() -> None:
    backend = BagOfWordsEmbeddingBackend()
    a = await backend.embed("hello trace lens optimization")
    b = await backend.embed("hello trace lens optimization!")
    score = cosine_similarity(a, b)
    assert score >= 0.92
