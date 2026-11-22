import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import ValidationError

from tracelens.api.deps import SessionDep
from tracelens.gateway.errors import (
    GatewayAuthError,
    GatewayRateLimitError,
    GatewayValidationError,
    ProviderError,
    openai_error_body,
)
from tracelens.gateway.streaming import stream_chat_response
from tracelens.pipeline.context import GatewayContext
from tracelens.pipeline.executor import build_chat_pipeline
from tracelens.providers.schemas import ChatCompletionRequest

router = APIRouter(tags=["gateway"])


@router.post("/v1/chat/completions", response_model=None)
async def chat_completions(request: Request, session: SessionDep) -> Response:
    try:
        payload = await request.json()
        chat_request = ChatCompletionRequest.model_validate(payload)
    except ValidationError as exc:
        return JSONResponse(
            status_code=400,
            content=_validation_error_body(exc),
        )

    context = GatewayContext(
        request_id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        chat_request=chat_request,
    )

    pipeline = build_chat_pipeline(session)
    stream_mode = chat_request.stream
    skip_trace = {"trace_enqueue"} if stream_mode else None

    try:
        await pipeline.run(request, context, skip=skip_trace)
    except GatewayAuthError as exc:
        return JSONResponse(status_code=401, content=openai_error_body(exc.message, code=exc.code))
    except GatewayRateLimitError as exc:
        return JSONResponse(
            status_code=429,
            content=openai_error_body(
                exc.message,
                code=exc.code,
                error_type="rate_limit_error",
            ),
        )
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

    if stream_mode:
        if context.stream_chunks is None:
            return JSONResponse(
                status_code=500,
                content=openai_error_body(
                    "Streaming source missing",
                    code="server_error",
                    error_type="server_error",
                ),
            )
        return StreamingResponse(
            stream_chat_response(request, context, context.stream_chunks),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
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
        "requested_model": context.requested_model,
        "selected_model": context.selected_model,
        "routing_explanation": context.routing_explanation,
    }
    return JSONResponse(status_code=200, content=body)


def _validation_error_body(exc: ValidationError) -> dict[str, object]:
    message = "; ".join(
        f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()
    )
    return openai_error_body(message, code="invalid_request_error")
