import re
from typing import Any

from tracelens.db.models.request_log import RequestLog
from tracelens.providers.schemas import ChatCompletionRequest, ChatCompletionResponse


def build_chat_request_from_log(row: RequestLog) -> ChatCompletionRequest:
    payload = row.request_payload or {}
    request_body = payload.get("request")
    if not isinstance(request_body, dict):
        raise ValueError("request_log missing replay request snapshot")
    return ChatCompletionRequest.model_validate(request_body)


def extract_logged_response_text(row: RequestLog) -> str | None:
    payload = row.request_payload or {}
    text = payload.get("response_text")
    return text if isinstance(text, str) else None


def normalize_completion_text(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    return collapsed


def diff_replay(
    *,
    original_text: str | None,
    replay_response: ChatCompletionResponse,
) -> dict[str, Any]:
    replay_text = replay_response.choices[0].message.content
    normalized_original = normalize_completion_text(original_text or "")
    normalized_replay = normalize_completion_text(replay_text)
    identical = normalized_original == normalized_replay
    return {
        "identical": identical,
        "original_text": original_text,
        "replay_text": replay_text,
        "normalized_match": identical,
    }
