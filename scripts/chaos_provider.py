#!/usr/bin/env python3
"""Chaos demo: force mock-gpt failures and observe fallback without client-visible errors."""

from __future__ import annotations

import argparse
import os
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="TraceLens provider chaos demo")
    parser.add_argument("--base-url", default=os.environ.get("TRACELENS_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--api-key", default=os.environ.get("TRACELENS_API_KEY", ""))
    parser.add_argument("--attempts", type=int, default=12)
    args = parser.parse_args()
    if not args.api_key:
        print("Set TRACELENS_API_KEY or pass --api-key", file=sys.stderr)
        return 1

    successes = 0
    fallbacks = 0
    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        for idx in range(args.attempts):
            response = client.post(
                "/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {args.api_key}",
                    "X-TraceLens-Mock-Error-Rate": "1.0",
                    "X-TraceLens-Mock-Error-Models": "mock-gpt",
                    "X-TraceLens-Mock-Seed": str(1000 + idx),
                },
                json={
                    "model": "mock-gpt",
                    "messages": [{"role": "user", "content": f"chaos ping {idx}"}],
                },
            )
            if response.status_code == 200:
                successes += 1
                body = response.json()
                meta = body.get("tracelens") or {}
                selected = meta.get("selected_model")
                attempts = (meta.get("routing_explanation") or {}).get("attempts") or []
                if selected != "mock-gpt":
                    fallbacks += 1
                print(
                    f"ok #{idx} status={response.status_code} "
                    f"selected={selected} attempts={len(attempts)}"
                )
            else:
                print(f"fail #{idx} status={response.status_code} body={response.text[:200]}")

    print(f"\nSummary: {successes}/{args.attempts} HTTP 200, {fallbacks} used fallback model")
    return 0 if successes == args.attempts else 2


if __name__ == "__main__":
    raise SystemExit(main())