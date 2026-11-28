from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

GATEWAY_REQUESTS = Counter(
    "tracelens_gateway_requests_total",
    "Total gateway chat requests",
    ["outcome"],
)

TRACE_ENQUEUE_TOTAL = Counter(
    "tracelens_trace_enqueue_total",
    "Trace enqueue attempts",
    ["result"],
)

TRACE_ENQUEUE_DURATION = Histogram(
    "tracelens_trace_enqueue_seconds",
    "Time spent enqueueing traces to Redis",
    buckets=(0.0005, 0.001, 0.002, 0.005, 0.01, 0.05, 0.1),
)

TRACE_WORKER_PROCESSED = Counter(
    "tracelens_trace_worker_processed_total",
    "Traces persisted by worker",
    ["result"],
)

EVAL_WORKER_PROCESSED = Counter(
    "tracelens_eval_worker_processed_total",
    "Eval jobs processed by worker",
    ["result"],
)


def metrics_response_body() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
