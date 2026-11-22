import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from tracelens.providers.schemas import ChatCompletionRequest, ChatCompletionResponse
from tracelens.security.budgets import UsageSnapshot


@dataclass
class GatewayContext:
    """Per-request gateway state populated by pipeline stages."""

    tenant_id: uuid.UUID | None = None
    key_id: uuid.UUID | None = None
    budget_id: uuid.UUID | None = None
    budget_snapshot: UsageSnapshot | None = None
    request_log_id: uuid.UUID | None = None
    bearer_token: str | None = None
    request_id: str | None = None
    chat_request: ChatCompletionRequest | None = None
    chat_response: ChatCompletionResponse | None = None
    stream_chunks: AsyncIterator[dict[str, Any]] | None = None
    allowed_models: list[str] = field(default_factory=list)
    client_ip: str | None = None
    requested_model: str | None = None
    selected_model: str | None = None
    route_candidates: list[str] = field(default_factory=list)
    routing_explanation: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    stages_executed: list[str] = field(default_factory=list)
