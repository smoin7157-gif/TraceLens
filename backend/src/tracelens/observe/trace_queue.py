from tracelens.pipeline.context import GatewayContext


async def enqueue_trace(_context: GatewayContext) -> None:
    """No-op trace queue for phase 4 (Redis worker arrives in phase 11)."""
    return None
