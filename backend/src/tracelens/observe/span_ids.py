import uuid


def span_hex_to_uuid(span_id: str) -> uuid.UUID:
    """Map W3C 16-hex span id (or 32-hex) to UUID for ORM primary keys."""
    cleaned = span_id.replace("-", "").lower()
    if len(cleaned) == 16:
        return uuid.UUID(hex=cleaned.zfill(32))
    if len(cleaned) == 32:
        return uuid.UUID(hex=cleaned)
    return uuid.UUID(cleaned)
