import uuid
from dataclasses import dataclass, field


@dataclass
class GatewayContext:
    """Per-request gateway state populated by pipeline stages."""

    tenant_id: uuid.UUID | None = None
    key_id: uuid.UUID | None = None
    bearer_token: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
