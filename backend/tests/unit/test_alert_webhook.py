import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tracelens.db.models.tenant import Tenant
from tracelens.observe.alerts import create_alert, fire_alert


@pytest.mark.integration
@pytest.mark.asyncio
async def test_alert_fires_webhook_on_spike(db_session) -> None:
    tenant_id = uuid.uuid4()
    db_session.add(Tenant(id=tenant_id, name="Alert", slug=f"al-{tenant_id.hex[:6]}"))
    alert = await create_alert(
        db_session,
        tenant_id,
        name="error spike",
        metric="error_rate",
        threshold=0.2,
        webhook_url="https://example.test/hook",
    )
    with patch("tracelens.observe.alerts._post_alert", new_callable=AsyncMock) as post_mock:
        event = await fire_alert(db_session, alert, observed_value=0.95)
        await db_session.commit()

    assert event.id is not None
    post_mock.assert_called_once()
