class TenantIsolationError(Exception):
    """Raised when an operation would read or write data outside the scoped tenant."""
