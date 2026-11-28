import uuid

import pytest

from tracelens.db.models.tenant import Tenant
from tracelens.observe.alerts import create_alert


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_alert_rejects_unsafe_webhook(db_session) -> None:
    tenant_id = uuid.uuid4()
    db_session.add(Tenant(id=tenant_id, name="T", slug=f"w-{tenant_id.hex[:6]}"))
    await db_session.flush()
    with pytest.raises(ValueError, match="not allowed"):
        await create_alert(
            db_session,
            tenant_id,
            name="x",
            metric="error_rate",
            threshold=0.5,
            webhook_url="http://127.0.0.1/hook",
        )