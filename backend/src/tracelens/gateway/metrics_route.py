from fastapi import APIRouter, Header, HTTPException, Response, status

from tracelens.config import get_settings
from tracelens.observe.metrics import metrics_response_body

router = APIRouter(tags=["observe"])


@router.get("/metrics")
async def prometheus_metrics(
    authorization: str | None = Header(default=None),
    x_metrics_token: str | None = Header(default=None, alias="X-Metrics-Token"),
) -> Response:
    token = get_settings().metrics_scrape_token
    if token:
        bearer = authorization.removeprefix("Bearer ").strip() if authorization else ""
        if bearer != token and x_metrics_token != token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Metrics scrape token required",
            )
    body, content_type = metrics_response_body()
    return Response(content=body, media_type=content_type)
