from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.config import get_settings
from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.stages.auth import AuthStage
from tracelens.pipeline.stages.base import PipelineStage
from tracelens.pipeline.stages.provider import ProviderStage
from tracelens.pipeline.stages.trace_enqueue import TraceEnqueueStage


class Pipeline:
    """Runs ordered gateway stages; disabled stages are skipped."""

    def __init__(self, stages: list[PipelineStage], toggles: dict[str, bool]) -> None:
        self._stages = stages
        self._toggles = toggles

    async def run(
        self,
        request: Request,
        context: GatewayContext,
        *,
        skip: set[str] | None = None,
    ) -> None:
        skip = skip or set()
        for stage in self._stages:
            if stage.name in skip:
                continue
            if not self._toggles.get(stage.name, True):
                continue
            await stage.run(request, context)
            context.stages_executed.append(stage.name)


def build_chat_pipeline(session: AsyncSession) -> Pipeline:
    settings = get_settings()
    toggles = settings.pipeline.model_dump()
    stages: list[PipelineStage] = [
        AuthStage(session),
        ProviderStage(session),
        TraceEnqueueStage(),
    ]
    return Pipeline(stages=stages, toggles=toggles)
