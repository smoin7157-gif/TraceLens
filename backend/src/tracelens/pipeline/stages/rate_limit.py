from fastapi import Request

from tracelens.config import get_settings
from tracelens.db.redis_client import RedisClient
from tracelens.gateway.errors import GatewayRateLimitError
from tracelens.pipeline.context import GatewayContext
from tracelens.security.rate_limit import check_rate_limits


class RateLimitStage:
    name = "rate_limit"

    async def run(self, request: Request, context: GatewayContext) -> None:
        if context.tenant_id is None or context.key_id is None:
            return

        settings = get_settings()
        redis = RedisClient.connection()
        try:
            allowed, reason = await check_rate_limits(
                redis,
                tenant_id=context.tenant_id,
                key_id=context.key_id,
                client_ip=context.client_ip,
            )
        except Exception as exc:
            if settings.security_policy.rate_limit_on_redis_failure == "open":
                context.metadata["rate_limit_fail_open"] = True
                return
            raise GatewayRateLimitError(
                "Rate limiting unavailable",
                code="rate_limit_exceeded",
            ) from exc

        if not allowed:
            raise GatewayRateLimitError(
                reason or "Rate limit exceeded",
                code="rate_limit_exceeded",
            )
