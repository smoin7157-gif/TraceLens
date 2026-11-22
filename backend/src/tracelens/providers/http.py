import httpx


def provider_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
