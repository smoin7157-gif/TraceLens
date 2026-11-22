from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from tracelens_sdk.context import trace_span

P = ParamSpec("P")
R = TypeVar("R")


def traced(name: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        span_name = name or fn.__qualname__

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with trace_span(span_name):
                return fn(*args, **kwargs)

        return wrapper

    return decorator