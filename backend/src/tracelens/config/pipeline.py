from pydantic import BaseModel


class PipelineToggles(BaseModel):
    """Per-stage enable flags (phase 4 defaults; more stages added later)."""

    auth: bool = True
    rate_limit: bool = True
    validation: bool = True
    security_scan: bool = True
    budget: bool = True
    router: bool = True
    provider: bool = True
    request_log: bool = True
    trace_enqueue: bool = True


def default_pipeline_toggles() -> PipelineToggles:
    return PipelineToggles()
