import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from tracelens.api.deps import SessionDep
from tracelens.gateway.errors import (
    GatewayAuthError,
    GatewayValidationError,
    ProviderError,
    openai_error_body,
)
from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.executor import build_chat_pipeline
from tracelens.providers.schemas import ChatCompletionRequest

router = APIRouter(tags=["gateway"])


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, session: SessionDep) -> JSONResponse:
    try:
        payload = await request.json()
        chat_request = ChatCompletionRequest.model_validate(payload)
    except ValidationError as exc:
        return JSONResponse(
            status_code=400,
            content=_validation_error_body(exc),
        )

    if chat_request.stream:
        return JSONResponse(
            status_code=400,
            content=openai_error_body(
                "Streaming is not supported yet (phase 6). Set stream=false.",
                code="stream_not_supported",
            ),
        )

    context = GatewayContext(
        request_id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        chat_request=chat_request,
    )

    try:
        pipeline = build_chat_pipeline(session)
        await pipeline.run(request, context)
    except GatewayAuthError as exc:
        return JSONResponse(status_code=401, content=openai_error_body(exc.message, code=exc.code))
    except GatewayValidationError as exc:
        return JSONResponse(
            status_code=400,
            content=openai_error_body(exc.message, code=exc.code),
        )
    except ProviderError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=openai_error_body(
                exc.message,
                code=exc.code,
                error_type=exc.error_type,
            ),
        )

    if context.chat_response is None:
        return JSONResponse(
            status_code=500,
            content=openai_error_body(
                "No completion produced",
                code="server_error",
                error_type="server_error",
            ),
        )

    body = context.chat_response.model_dump()
    body["tracelens"] = {
        "tenant_id": str(context.tenant_id) if context.tenant_id else None,
        "stages": context.stages_executed,
    }
    return JSONResponse(status_code=200, content=body)


def _validation_error_body(exc: ValidationError) -> dict[str, object]:
    message = "; ".join(
        f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()
    )
    return openai_error_body(message, code="invalid_request_error")
