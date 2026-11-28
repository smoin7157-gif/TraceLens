#!/usr/bin/env python3
"""Seed dashboard demo tenant via admin API (compose-friendly)."""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed TraceLens demo tenant")
    parser.add_argument("--base-url", default=os.environ.get("TRACELENS_BASE_URL", "http://localhost:8000"))
    parser.add_argument(
        "--admin-token",
        default=os.environ.get("ADMIN_API_TOKEN", "change-me-in-production"),
    )
    args = parser.parse_args()

    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        health = client.get("/health")
        health.raise_for_status()
        ready = client.get("/health/ready", timeout=30.0)
        if ready.status_code != 200:
            print("API not ready:", ready.text, file=sys.stderr)
            return 1
        response = client.post(
            "/dashboard/demo/seed",
            headers={"X-Admin-Token": args.admin_token},
        )
        if response.status_code >= 400:
            print(response.text, file=sys.stderr)
            return response.status_code
        payload = response.json()
        print(json.dumps(payload, indent=2))
        print("\nSet dashboard Settings tenant_id to:", payload.get("tenant_id"))
        print("Gateway API key:", payload.get("api_key_secret"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())