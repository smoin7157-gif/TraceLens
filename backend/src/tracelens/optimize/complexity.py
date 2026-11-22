from tracelens.providers.schemas import ChatMessage


def complexity_score(messages: list[ChatMessage]) -> float:
    text = "\n".join(m.content for m in messages)
    words = len(text.split())
    score = float(words)
    if "```" in text or "def " in text or "class " in text:
        score += 50.0
    if any(len(m.content) > 2000 for m in messages):
        score += 40.0
    return score
