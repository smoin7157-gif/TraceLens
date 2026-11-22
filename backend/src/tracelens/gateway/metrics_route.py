from fastapi import APIRouter, Response

from tracelens.observe.metrics import metrics_response_body

router = APIRouter(tags=["observe"])


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    body, content_type = metrics_response_body()
    return Response(content=body, media_type=content_type)
