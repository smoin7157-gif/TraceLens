from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.config import get_settings
from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.stages.auth import AuthStage
from tracelens.pipeline.stages.base import PipelineStage
from tracelens.pipeline.stages.budget import BudgetStage
from tracelens.pipeline.stages.cache_lookup import CacheLookupStage
from tracelens.pipeline.stages.cache_write import CacheWriteStage
from tracelens.pipeline.stages.optimizer import OptimizerStage
from tracelens.pipeline.stages.provider_call import ProviderCallStage
from tracelens.pipeline.stages.rate_limit import RateLimitStage
from tracelens.pipeline.stages.request_log import RequestLogStage
from tracelens.pipeline.stages.router import RouterStage
from tracelens.pipeline.stages.security_scan import SecurityScanStage
from tracelens.pipeline.stages.trace_enqueue import TraceEnqueueStage
from tracelens.pipeline.stages.validation import ValidationStage


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
        RateLimitStage(),
        ValidationStage(),
        SecurityScanStage(),
        BudgetStage(session),
        OptimizerStage(),
        RouterStage(),
        CacheLookupStage(session),
        ProviderCallStage(session),
        CacheWriteStage(session),
        RequestLogStage(session),
        TraceEnqueueStage(),
    ]
    return Pipeline(stages=stages, toggles=toggles)
