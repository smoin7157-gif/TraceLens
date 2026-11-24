#!/usr/bin/env python3
"""Generate light demo traffic for dashboard live metrics."""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="TraceLens demo traffic generator")
    parser.add_argument("--base-url", default=os.environ.get("TRACELENS_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--api-key", default=os.environ.get("TRACELENS_API_KEY", ""))
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--sleep-ms", type=int, default=200)
    args = parser.parse_args()
    if not args.api_key:
        print("Set TRACELENS_API_KEY or pass --api-key", file=sys.stderr)
        return 1

    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        for idx in range(args.count):
            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {args.api_key}"},
                json={
                    "model": "mock-gpt",
                    "messages": [{"role": "user", "content": f"demo traffic {idx}"}],
                },
            )
            print(f"#{idx} -> {response.status_code}")
            time.sleep(args.sleep_ms / 1000.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())