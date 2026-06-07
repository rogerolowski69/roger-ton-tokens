#!/usr/bin/env python3
"""Local smoke test — run while API is up on :3001 with Postgres."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from urllib.parse import urlencode

import httpx

from apps.api.config import settings


def make_init_data(user_id: int = 42) -> str:
    user = json.dumps({"id": user_id, "username": "localtest", "first_name": "Local"})
    auth_date = str(int(time.time()))
    params = {"auth_date": auth_date, "user": user}
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


async def main() -> None:
    base = settings.api_base_url.rstrip("/")
    init = make_init_data()
    webhook_secret = settings.telegram_webhook_secret

    async with httpx.AsyncClient(base_url=base, timeout=30) as client:
        r = await client.get("/ready")
        assert r.status_code == 200 and r.json()["ok"] is True
        print("✓ GET /ready")

        r = await client.get("/api/checkout/balance", headers={"X-Telegram-Init-Data": init})
        assert r.status_code == 200, r.text
        bal = r.json()
        assert bal["balance_cents"] == 0
        print(f"✓ GET /api/checkout/balance → ${bal['balance_usd']}")

        r = await client.post(
            "/api/checkout/store-credit/pay",
            headers={"X-Telegram-Init-Data": init, "Content-Type": "application/json"},
            json={"sku": "hour_voucher_1h"},
        )
        assert r.status_code == 402, r.text
        print("✓ POST store-credit/pay → 402 insufficient credit")

        r = await client.post("/api/webhooks/telegram", json={})
        assert r.status_code == 401
        print("✓ Webhook rejects missing secret")

        from apps.api.db import SessionLocal
        from apps.api.models.order import PROVIDER_TELEGRAM_STARS
        from apps.api.services.orders import create_order_for_sku, seed_products

        async with SessionLocal() as db:
            await seed_products(db)

        async with SessionLocal() as db:
            order = await create_order_for_sku(
                db, telegram_user_id=42, sku="credit_1_usd", provider=PROVIDER_TELEGRAM_STARS
            )
            order_id = order.id

        charge_id = f"test_charge_{uuid.uuid4().hex[:8]}"
        payload = {
            "message": {
                "chat": {"id": 42},
                "from": {"id": 42},
                "successful_payment": {
                    "currency": "XTR",
                    "total_amount": 50,
                    "invoice_payload": str(order_id),
                    "telegram_payment_charge_id": charge_id,
                },
            }
        }
        r = await client.post(
            "/api/webhooks/telegram",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": webhook_secret},
        )
        assert r.status_code == 200, r.text
        print("✓ Webhook successful_payment → 200")

        r = await client.get("/api/checkout/balance", headers={"X-Telegram-Init-Data": init})
        bal = r.json()
        assert bal["balance_cents"] == 100, bal
        print(f"✓ Balance after Stars payment → ${bal['balance_usd']}")

        r = await client.post(
            "/api/checkout/store-credit/pay",
            headers={"X-Telegram-Init-Data": init, "Content-Type": "application/json"},
            json={"sku": "hour_voucher_1h"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        print(f"✓ Store credit purchase → status={data['status']}")

        r = await client.get("/api/checkout/balance", headers={"X-Telegram-Init-Data": init})
        assert r.json()["balance_cents"] == 0
        print("✓ Balance after spend → $0.00")

        r = await client.post(
            "/api/webhooks/telegram",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": webhook_secret},
        )
        assert r.status_code == 200
        r = await client.get("/api/checkout/balance", headers={"X-Telegram-Init-Data": init})
        assert r.json()["balance_cents"] == 0
        print("✓ Idempotent webhook — no double credit")

    print("\nAll local smoke tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
