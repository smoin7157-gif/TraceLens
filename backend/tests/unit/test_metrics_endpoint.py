import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.main import app


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_counters() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert "tracelens_trace_enqueue_total" in body
    assert "tracelens_cache_lookup_total" in body
    assert "tracelens_trace_dlq_total" in body
