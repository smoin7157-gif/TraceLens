from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.repositories.api_key import ApiKeyAuthRepository
from tracelens.gateway.errors import GatewayAuthError
from tracelens.pipeline.context import GatewayContext
from tracelens.security.keys import mask_api_key, parse_api_key, verify_api_key


class AuthStage:
    """Pipeline stage 1: resolve Authorization bearer to tenant + key id."""

    name = "auth"

    def __init__(self, session: AsyncSession) -> None:
        self._keys = ApiKeyAuthRepository(session)

    async def run(self, request: Request, context: GatewayContext) -> None:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise GatewayAuthError(
                "You didn't provide an API key. You need to provide your API key in an "
                "Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY).",
                code="missing_api_key",
            )

        raw_key = authorization.removeprefix("Bearer ").strip()
        if not raw_key:
            raise GatewayAuthError(
                "You didn't provide an API key.",
                code="missing_api_key",
            )

        parsed = parse_api_key(raw_key)
        if parsed is None:
            raise GatewayAuthError(
                f"Incorrect API key provided: {mask_api_key(raw_key)}. You can find your API key "
                "at TraceLens admin settings.",
            )

        key_prefix, normalized = parsed
        context.bearer_token = normalized

        candidates = await self._keys.find_active_by_prefix(key_prefix)
        for candidate in candidates:
            if verify_api_key(normalized, candidate.key_hash):
                context.tenant_id = candidate.tenant_id
                context.key_id = candidate.id
                context.allowed_models = list(candidate.allowed_models or [])
                if request.client is not None:
                    context.client_ip = request.client.host
                return

        raise GatewayAuthError(
            f"Incorrect API key provided: {mask_api_key(normalized)}. You can find your API key "
            "at TraceLens admin settings.",
        )
