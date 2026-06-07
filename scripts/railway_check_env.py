#!/usr/bin/env python3
"""Validate env vars before Railway deploy or post-deploy webhook setup."""
from __future__ import annotations

import os

REQUIRED = (
    "DATABASE_URL",
    "BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "API_BASE_URL",
    "MINI_APP_URL",
)

OPTIONAL = (
    "MERCHANT_TON_WALLET",
    "JETTON_MASTER_ADDRESS",
    "ALLOWED_ORIGINS",
    "PORT",
)


def main() -> int:
    missing = [key for key in REQUIRED if not os.getenv(key)]
    if missing:
        print("Missing required environment variables:")
        for key in missing:
            print(f"  - {key}")
        return 1

    print("Required variables: OK")
    for key in OPTIONAL:
        value = os.getenv(key)
        if value:
            print(f"  {key}=set")
        else:
            print(f"  {key}= (optional, not set)")

    db = os.environ["DATABASE_URL"]
    if db.startswith("postgres://") or (
        db.startswith("postgresql://") and "+asyncpg" not in db
    ):
        print("DATABASE_URL: Railway Postgres URL detected (app normalizes to asyncpg)")

    api = os.environ["API_BASE_URL"].rstrip("/")
    print(f"Webhook URL will be: {api}/api/webhooks/telegram")
    print(f"Health check: {api}/health")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
