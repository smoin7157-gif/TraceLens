# Interview OS → TraceLens

Interview OS sessions that call LLMs can share one TraceLens tenant for cost caps, security scanning, and trace review.

## Setup

1. `python scripts/seed_demo.py` or create a tenant + API key via admin APIs.
2. Configure Interview OS to use `TRACELENS_BASE_URL` + bearer key (OpenAI SDK compatible).

## Session tracing

Enable W3C `traceparent` on responses and propagate to downstream services:

```http
traceparent: 00-{trace_id}-{span_id}-01
```

Link dashboard **Trace Explorer** spans to Interview OS session IDs via request tags (future: custom metadata header).

## Eval loop

1. Import high-signal `requests_log` rows into a dataset.
2. Run an experiment across prompt versions (`/admin/.../experiments`).
3. Let `eval_worker` update Redis quality scores consumed by the router.

## Compliance notes

- Set `PII_MODE=block` (default) before production interview content.
- Use `X-TraceLens-Cache-Bypass: 1` on verbatim scoring prompts where caching is unsafe (see gateway optimizer docs in `PLAN.md`).