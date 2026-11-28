from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from tracelens.db.redis_client import RedisClient
from tracelens.db.session import get_engine

router = APIRouter(tags=["health"])


@router.get("/health/ready")
async def health_ready() -> dict[str, Any]:
    """Readiness: Postgres + Redis must answer."""
    checks: dict[str, str] = {}
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "error"

    try:
        redis = RedisClient.connection()
        if await redis.ping():
            checks["redis"] = "ok"
        else:
            checks["redis"] = "error"
    except Exception:
        checks["redis"] = "error"

    ready = all(value == "ok" for value in checks.values())
    return {"status": "ready" if ready else "degraded", "checks": checks}
