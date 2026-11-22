import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import ValidationError

from tracelens.api.deps import SessionDep
from tracelens.gateway.errors import (
    GatewayAuthError,
    GatewayBudgetError,
    GatewayRateLimitError,
    GatewayValidationError,
    ProviderError,
    openai_error_body,
)
from tracelens.gateway.streaming import stream_chat_response
from tracelens.observe.metrics import GATEWAY_REQUESTS
from tracelens.observe.request_log import persist_request_log
from tracelens.observe.traces import format_traceparent, init_trace_context
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
    init_trace_context(request, context)

    pipeline = build_chat_pipeline(session)
    stream_mode = chat_request.stream
    skip_end_stages = {"trace_enqueue", "request_log"} if stream_mode else None

    try:
        await pipeline.run(request, context, skip=skip_end_stages)
    except GatewayAuthError as exc:
        GATEWAY_REQUESTS.labels(outcome="auth_error").inc()
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
    except GatewayBudgetError as exc:
        await persist_request_log(
            session,
            context,
            status="budget_exceeded",
            record_budget_usage=False,
        )
        return JSONResponse(
            status_code=429,
            content=openai_error_body(
                exc.message,
                code=exc.code,
                error_type="insufficient_quota",
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
            stream_chat_response(request, context, context.stream_chunks, session=session),
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
    GATEWAY_REQUESTS.labels(outcome="success").inc()
    trace_headers: dict[str, str] = {}
    if context.trace_id and context.root_span_id:
        trace_headers["traceparent"] = format_traceparent(context.trace_id, context.root_span_id)

    body["tracelens"] = {
        "tenant_id": str(context.tenant_id) if context.tenant_id else None,
        "trace_id": context.trace_id,
        "stages": context.stages_executed,
        "requested_model": context.requested_model,
        "selected_model": context.selected_model,
        "routing_explanation": context.routing_explanation,
        "cache_status": context.cache_status,
        "optimizations_applied": context.optimizations_applied,
        "cost_actual": str(context.cost_actual),
        "cost_without_optimization": str(context.cost_without_optimization),
        "savings_usd": str(context.cost_without_optimization - context.cost_actual),
    }
    return JSONResponse(status_code=200, content=body, headers=trace_headers)


def _validation_error_body(exc: ValidationError) -> dict[str, object]:
    message = "; ".join(
        f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()
    )
    return openai_error_body(message, code="invalid_request_error")
