import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from tracelens.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dashboard_unknown_tenant_returns_404(db_session) -> None:
    unknown = uuid.uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/dashboard/overview?tenant_id={unknown}")
    assert response.status_code == 404
