import ipaddress
from urllib.parse import urlparse


class UnsafeWebhookError(ValueError):
    pass


def validate_webhook_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"https", "http"}:
        raise UnsafeWebhookError("Webhook URL must use http or https")
    host = (parsed.hostname or "").lower()
    if not host:
        raise UnsafeWebhookError("Webhook URL missing host")
    blocked_hosts = {
        "localhost",
        "metadata.google.internal",
        "metadata.google",
        "169.254.169.254",
    }
    if host in blocked_hosts or host.endswith(".local"):
        raise UnsafeWebhookError("Webhook host not allowed")
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return url.strip()
    if addr.is_private or addr.is_loopback or addr.is_link_local:
        raise UnsafeWebhookError("Webhook must not target private IP space")
    return url.strip()