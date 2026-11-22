import re
from typing import Protocol

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(system|prior)\s+prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+.*mode", re.IGNORECASE),
]


class InjectionClassifier(Protocol):
    def is_injection(self, text: str) -> bool: ...


class HeuristicInjectionClassifier:
    """Default heuristic hook; replaceable in later phases / admin config."""

    def __init__(self, patterns: list[re.Pattern[str]] | None = None) -> None:
        self._patterns = patterns or _INJECTION_PATTERNS

    def is_injection(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in self._patterns)


def scan_messages_for_injection(
    messages: list[str],
    classifier: InjectionClassifier | None = None,
) -> bool:
    clf = classifier or HeuristicInjectionClassifier()
    return any(clf.is_injection(message) for message in messages)
