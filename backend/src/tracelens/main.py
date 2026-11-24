from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tracelens import __version__
from tracelens.api import admin_budgets, admin_keys, admin_observe, dashboard, gateway_probe
from tracelens.config import get_settings
from tracelens.gateway import chat, metrics_route, models
from tracelens.gateway import health as provider_health
from tracelens.gateway.errors import GatewayAuthError, openai_error_body
from tracelens.logging_setup import setup_logging

settings = get_settings()
setup_logging()

app = FastAPI(
    title="TraceLens",
    description="Self-hostable LLM gateway with observability and cost optimization",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_keys.router)
app.include_router(admin_budgets.router)
app.include_router(admin_observe.router)
app.include_router(gateway_probe.router)
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(provider_health.router)
app.include_router(metrics_route.router)
app.include_router(dashboard.router)


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
