from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.config import get_settings
from tracelens.db.session import get_session
from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.stages.auth import AuthStage

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_gateway_context(request: Request, session: SessionDep) -> GatewayContext:
    context = GatewayContext()
    await AuthStage(session).run(request, context)
    return context


GatewayContextDep = Annotated[GatewayContext, Depends(get_gateway_context)]


def require_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")) -> None:
    settings = get_settings()
    if not settings.admin_api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API disabled (set ADMIN_API_TOKEN)",
        )
    if not x_admin_token or x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")


AdminDep = Annotated[None, Depends(require_admin)]
