import json
import time
from collections import deque
from dataclasses import dataclass

_ring: deque[tuple[float, str]] = deque(maxlen=5000)


def record_gateway_outcome(outcome: str) -> None:
    _ring.append((time.time(), outcome))


def snapshot(window_seconds: int = 60) -> dict[str, float]:
    if not _ring:
        return {"requests_per_second": 0.0, "success_rate": 1.0, "sample_count": 0.0}
    now = time.time()
    window_start = now - window_seconds
    total = 0
    successes = 0
    for ts, outcome in _ring:
        if ts < window_start:
            continue
        total += 1
        if outcome == "success":
            successes += 1
    if total == 0:
        return {"requests_per_second": 0.0, "success_rate": 1.0, "sample_count": 0.0}
    rps = total / float(window_seconds)
    success_rate = successes / total
    return {
        "requests_per_second": round(rps, 4),
        "success_rate": round(success_rate, 4),
        "sample_count": float(total),
    }


def snapshot_json(window_seconds: int = 60) -> str:
    return json.dumps(snapshot(window_seconds), separators=(",", ":"))


@dataclass(frozen=True)
class LiveMetricsTick:
    requests_per_second: float
    success_rate: float
    sample_count: float
