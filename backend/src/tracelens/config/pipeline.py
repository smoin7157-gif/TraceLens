from pydantic import BaseModel


class PipelineToggles(BaseModel):
    """Per-stage enable flags (phase 4 defaults; more stages added later)."""

    auth: bool = True
    provider: bool = True
    trace_enqueue: bool = True


def default_pipeline_toggles() -> PipelineToggles:
    return PipelineToggles()
