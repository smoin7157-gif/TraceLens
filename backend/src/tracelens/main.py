from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from tracelens import __version__
from tracelens.api import admin_keys, gateway_probe
from tracelens.config import get_settings
from tracelens.gateway import chat, models
from tracelens.gateway import health as provider_health
from tracelens.gateway.errors import GatewayAuthError, openai_error_body

settings = get_settings()

app = FastAPI(
    title="TraceLens",
    description="Self-hostable LLM gateway with observability and cost optimization",
    version=__version__,
)

app.include_router(admin_keys.router)
app.include_router(gateway_probe.router)
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(provider_health.router)


@app.exception_handler(GatewayAuthError)
async def handle_gateway_auth(_request: Request, exc: GatewayAuthError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=openai_error_body(exc.message, code=exc.code),
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
