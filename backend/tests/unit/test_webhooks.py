import pytest

from tracelens.security.webhooks import UnsafeWebhookError, validate_webhook_url


def test_webhook_accepts_public_https() -> None:
    assert validate_webhook_url("https://hooks.example.com/alerts") == "https://hooks.example.com/alerts"


def test_webhook_rejects_localhost() -> None:
    with pytest.raises(UnsafeWebhookError):
        validate_webhook_url("http://localhost:8080/hook")


def test_webhook_rejects_metadata_ip() -> None:
    with pytest.raises(UnsafeWebhookError):
        validate_webhook_url("http://169.254.169.254/latest/meta-data/")


def test_webhook_rejects_private_ip_literal() -> None:
    with pytest.raises(UnsafeWebhookError):
        validate_webhook_url("https://10.0.0.5/internal")