from unittest.mock import MagicMock

import pytest
from fastapi import Request

from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.executor import Pipeline
from tracelens.providers.schemas import ChatCompletionRequest, ChatMessage


class _RecordingStage:
    def __init__(self, name: str) -> None:
        self.name = name

    async def run(self, _request: Request, context: GatewayContext) -> None:
        context.metadata[self.name] = "ran"


@pytest.mark.asyncio
async def test_pipeline_runs_stages_in_order() -> None:
    stages = [_RecordingStage("a"), _RecordingStage("b"), _RecordingStage("c")]
    pipeline = Pipeline(stages=stages, toggles={"a": True, "b": True, "c": True})
    context = GatewayContext(
        chat_request=ChatCompletionRequest(
            model="mock-gpt", messages=[ChatMessage(role="user", content="hi")]
        ),
    )

    await pipeline.run(MagicMock(spec=Request), context)

    assert context.stages_executed == ["a", "b", "c"]
    assert context.metadata == {"a": "ran", "b": "ran", "c": "ran"}


@pytest.mark.asyncio
async def test_pipeline_skips_disabled_stage() -> None:
    stages = [_RecordingStage("a"), _RecordingStage("b"), _RecordingStage("c")]
    pipeline = Pipeline(stages=stages, toggles={"a": True, "b": False, "c": True})
    context = GatewayContext()

    await pipeline.run(MagicMock(spec=Request), context)

    assert context.stages_executed == ["a", "c"]
    assert "b" not in context.metadata
