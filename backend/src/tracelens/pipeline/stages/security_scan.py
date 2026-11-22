from fastapi import Request

from tracelens.config import get_settings
from tracelens.gateway.errors import GatewayValidationError
from tracelens.pipeline.context import GatewayContext
from tracelens.providers.schemas import ChatMessage
from tracelens.security.injection import HeuristicInjectionClassifier, scan_messages_for_injection
from tracelens.security.pii import apply_pii_policy


class SecurityScanStage:
    name = "security_scan"

    def __init__(self, classifier: HeuristicInjectionClassifier | None = None) -> None:
        self._classifier = classifier or HeuristicInjectionClassifier()

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.chat_request is None:
            return

        settings = get_settings()
        texts = [message.content for message in context.chat_request.messages]

        if scan_messages_for_injection(texts, self._classifier):
            context.metadata["injection_detected"] = True
            if settings.injection_action == "block":
                raise GatewayValidationError(
                    "Prompt rejected by security policy (injection heuristic).",
                    code="injection_detected",
                )

        updated_messages: list[ChatMessage] = []
        pii_hits = 0
        for message in context.chat_request.messages:
            new_content, detected = apply_pii_policy(message.content, settings.pii_mode)
            if detected:
                pii_hits += 1
                if settings.pii_mode == "block":
                    raise GatewayValidationError(
                        "Prompt rejected by security policy (PII detected).",
                        code="pii_detected",
                    )
                if settings.pii_mode == "log_only":
                    context.metadata["pii_detected"] = True
                    updated_messages.append(message)
                    continue
            updated_messages.append(message.model_copy(update={"content": new_content}))

        if pii_hits:
            context.metadata["pii_hits"] = pii_hits
        context.chat_request = context.chat_request.model_copy(
            update={"messages": updated_messages}
        )
