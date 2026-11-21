from typing import Any

from fastapi import FastAPI

from tracelens import __version__
from tracelens.config import get_settings

settings = get_settings()

app = FastAPI(
    title="TraceLens",
    description="Self-hostable LLM gateway with observability and cost optimization",
    version=__version__,
)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Liveness check for load balancers and Docker health."""
    return {
        "status": "ok",
        "service": "tracelens-api",
        "version": __version__,
        "environment": settings.app_env,
    }
