from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from tracelens.config import get_settings


class DashboardReadGateMiddleware(BaseHTTPMiddleware):
    """Optional bearer gate for dashboard BFF (except public SSE live stream)."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        if not path.startswith("/dashboard"):
            return await call_next(request)
        if path == "/dashboard/live":
            return await call_next(request)

        token = get_settings().dashboard_read_token
        if not token:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {token}" and request.headers.get("X-Dashboard-Token") != token:
            return JSONResponse(
                status_code=401, content={"detail": "Dashboard read token required"}
            )
        return await call_next(request)
