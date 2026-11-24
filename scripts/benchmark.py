#!/usr/bin/env python3
"""Print a simple latency table against the TraceLens gateway."""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="TraceLens gateway benchmark")
    parser.add_argument("--base-url", default=os.environ.get("TRACELENS_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--api-key", default=os.environ.get("TRACELENS_API_KEY", ""))
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--model", default="mock-gpt")
    args = parser.parse_args()
    if not args.api_key:
        print("Set TRACELENS_API_KEY or pass --api-key", file=sys.stderr)
        return 1

    latencies_ms: list[float] = []
    with httpx.Client(base_url=args.base_url, timeout=60.0) as client:
        for idx in range(args.requests):
            started = time.perf_counter()
            response = client.post(
                "/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {args.api_key}",
                    "X-TraceLens-Mock-Latency-Ms": "1",
                },
                json={
                    "model": args.model,
                    "messages": [{"role": "user", "content": f"bench {idx}"}],
                },
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if response.status_code != 200:
                print(f"request {idx} failed: {response.status_code}")
                return 2
            latencies_ms.append(elapsed_ms)

    print(f"Model: {args.model}")
    print(f"Requests: {args.requests}")
    print(f"p50_ms: {statistics.median(latencies_ms):.2f}")
    print(f"mean_ms: {statistics.mean(latencies_ms):.2f}")
    if len(latencies_ms) >= 2:
        print(f"p95_ms: {statistics.quantiles(latencies_ms, n=20)[-1]:.2f}")
    print(f"min_ms: {min(latencies_ms):.2f} max_ms: {max(latencies_ms):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())