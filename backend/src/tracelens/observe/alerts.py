import asyncio
import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from tracelens.db.models.alert import Alert, AlertEvent
from tracelens.security.webhooks import UnsafeWebhookError, validate_webhook_url


async def create_alert(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str,
    metric: str,
    threshold: float,
    webhook_url: str,
) -> Alert:
    try:
        safe_url = validate_webhook_url(webhook_url)
    except UnsafeWebhookError as exc:
        raise ValueError(str(exc)) from exc
    alert = Alert(
        tenant_id=tenant_id,
        name=name,
        metric=metric,
        threshold=threshold,
        webhook_url=safe_url,
    )
    session.add(alert)
    await session.flush()
    return alert


async def fire_alert(
    session: AsyncSession,
    alert: Alert,
    *,
    observed_value: float,
    extra: dict[str, object] | None = None,
) -> AlertEvent:
    payload = {
        "alert_id": str(alert.id),
        "metric": alert.metric,
        "threshold": alert.threshold,
        "observed_value": observed_value,
        **(extra or {}),
    }
    event = AlertEvent(
        tenant_id=alert.tenant_id,
        alert_id=alert.id,
        payload=payload,
    )
    session.add(event)
    await session.flush()
    asyncio.create_task(_post_alert(alert.webhook_url, payload))
    return event


async def _post_alert(url: str, payload: dict[str, object]) -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json=payload)
    except Exception:
        return None
