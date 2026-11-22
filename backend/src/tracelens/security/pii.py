import re

from tracelens.config.security import PiiMode

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


def contains_pii(text: str) -> bool:
    return bool(_EMAIL_RE.search(text) or _SSN_RE.search(text) or _PHONE_RE.search(text))


def redact_pii(text: str) -> str:
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = _SSN_RE.sub("[REDACTED_SSN]", redacted)
    return _PHONE_RE.sub("[REDACTED_PHONE]", redacted)


def apply_pii_policy(text: str, mode: PiiMode) -> tuple[str, bool]:
    """Return updated text and whether PII was detected."""
    if not contains_pii(text):
        return text, False
    if mode == "redact":
        return redact_pii(text), True
    return text, True
