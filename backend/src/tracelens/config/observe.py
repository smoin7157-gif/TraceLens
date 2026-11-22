from pydantic import BaseModel, Field


class ObservePolicy(BaseModel):
    trace_queue_key: str = "tl:trace:queue"
    eval_queue_key: str = "tl:eval:queue"
    trace_enqueue_fail_open: bool = True
    worker_batch_size: int = Field(default=16, ge=1)
    worker_poll_timeout_seconds: int = Field(default=2, ge=1)
    json_logs: bool = True
