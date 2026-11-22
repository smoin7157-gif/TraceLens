from fastapi import APIRouter
from fastapi.responses import JSONResponse

from tracelens.api.deps import GatewayContextDep, SessionDep
from tracelens.providers.anthropic import AnthropicProvider
from tracelens.providers.credentials import resolve_api_key
from tracelens.providers.gemini import GeminiProvider
from tracelens.providers.openai import OpenAIProvider

router = APIRouter(tags=["gateway"])


@router.get("/v1/models")
async def list_models(_context: GatewayContextDep, session: SessionDep) -> JSONResponse:
    models: list[dict[str, str]] = [
        {"id": "mock-gpt", "object": "model", "owned_by": "tracelens"},
        {"id": "mock-gpt-4", "object": "model", "owned_by": "tracelens"},
    ]

    openai_key = await resolve_api_key(session, "openai")
    if openai_key:
        try:
            models.extend(await OpenAIProvider(openai_key).list_models())
        except Exception:
            models.append({"id": "gpt-4o-mini", "object": "model", "owned_by": "openai"})

    if await resolve_api_key(session, "anthropic"):
        models.extend(AnthropicProvider("x").static_models())

    if await resolve_api_key(session, "gemini"):
        models.extend(GeminiProvider("x").static_models())

    return JSONResponse(status_code=200, content={"object": "list", "data": models})
