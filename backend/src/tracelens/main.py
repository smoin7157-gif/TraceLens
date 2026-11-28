import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from tracelens import __version__
from tracelens.api import (
    admin_budgets,
    admin_cache,
    admin_config,
    admin_dlq,
    admin_keys,
    admin_observe,
    admin_replay,
    admin_tenants,
    dashboard,
    gateway_probe,
    health_ready,
)
from tracelens.config import get_settings
from tracelens.gateway import chat, metrics_route, models
from tracelens.gateway import health as provider_health
from tracelens.gateway.errors import GatewayAuthError, openai_error_body
from tracelens.logging_setup import setup_logging
from tracelens.middleware.dashboard_gate import DashboardReadGateMiddleware
from tracelens.middleware.request_id import RequestIdMiddleware
from tracelens.middleware.security_headers import SecurityHeadersMiddleware

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TraceLens",
    description="Self-hostable LLM gateway with observability and cost optimization",
    version=__version__,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(DashboardReadGateMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_keys.router)
app.include_router(admin_tenants.router)
app.include_router(admin_budgets.router)
app.include_router(admin_observe.router)
app.include_router(admin_config.router)
app.include_router(admin_replay.router)
app.include_router(admin_cache.router)
app.include_router(admin_dlq.router)
app.include_router(gateway_probe.router)
app.include_router(health_ready.router)
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


@app.exception_handler(Exception)
async def handle_unexpected(_request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(_request.state, "request_id", None)
    logger.exception("unhandled_error", extra={"request_id": request_id})
    body = openai_error_body(
        "Internal server error",
        code="server_error",
        error_type="server_error",
    )
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(status_code=500, content=body)


@app.get("/health")
async def health() -> dict[str, Any]:
    """Liveness check for load balancers and Docker health."""
    return {
        "status": "ok",
        "service": "tracelens-api",
        "version": __version__,
        "environment": settings.app_env,
    }
