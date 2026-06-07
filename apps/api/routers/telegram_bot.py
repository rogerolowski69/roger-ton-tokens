from __future__ import annotations

import contextlib
import hmac
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.db import get_db
from apps.api.models.order import PROVIDER_TELEGRAM_STARS
from apps.api.services import telegram_api
from apps.api.services.orders import (
    create_order_for_sku,
    fulfill_order_from_payment,
    get_credit_balance_cents,
    validate_order_for_checkout,
)

router = APIRouter(prefix="/api/webhooks/telegram", tags=["telegram"])


async def _tg(method: str, payload: dict[str, Any]) -> Any:
    return await telegram_api.tg(method, payload)


async def send_start_menu(chat_id: int) -> None:
    await telegram_api.send_message(
        chat_id,
        (
            "Roger TON Tokens\n\n"
            "Quick actions:\n"
            "/balance — store credit\n"
            "/buy_credit — buy $1 website credit\n"
            "/buy_hour — buy 1-hour time voucher\n"
            "/help — commands list"
        ),
        reply_markup={
            "inline_keyboard": [
                [{"text": "Open Mini App", "web_app": {"url": settings.mini_app_url}}],
                [{"text": "Buy $1 Credit ⭐", "callback_data": "stars:credit_1_usd"}],
                [{"text": "Buy 1-Hour Voucher ⭐", "callback_data": "stars:hour_voucher_1h"}],
            ]
        },
    )


async def send_stars_invoice(
    db: AsyncSession,
    *,
    chat_id: int,
    telegram_user_id: int,
    sku: str,
) -> None:
    order = await create_order_for_sku(
        db,
        telegram_user_id=telegram_user_id,
        sku=sku,
        provider=PROVIDER_TELEGRAM_STARS,
    )

    await telegram_api.send_invoice(
        chat_id=chat_id,
        title="Roger Token Purchase",
        description=f"Purchase: {sku}",
        payload=str(order.id),
        currency="XTR",
        prices=[{"label": sku, "amount": int(order.expected_amount)}],
    )


@router.post("")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    if not x_telegram_bot_api_secret_token:
        raise HTTPException(status_code=401, detail="Missing webhook secret")

    if not hmac.compare_digest(
        x_telegram_bot_api_secret_token,
        settings.telegram_webhook_secret,
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    update = await request.json()

    message = update.get("message")
    callback_query = update.get("callback_query")
    pre_checkout_query = update.get("pre_checkout_query")

    if message:
        chat_id = message["chat"]["id"]
        from_user = message.get("from") or {}
        telegram_user_id = int(from_user.get("id") or 0)
        text = message.get("text", "")

        if text.startswith("/start") or text.startswith("/app"):
            await send_start_menu(chat_id)

        elif text.startswith("/help"):
            await telegram_api.send_message(
                chat_id,
                (
                    "Commands:\n"
                    "/balance — store credit\n"
                    "/buy_credit — Stars checkout for $1 credit\n"
                    "/buy_hour — Stars checkout for 1-hour voucher\n"
                    "/app — open Mini App"
                ),
            )

        elif text.startswith("/balance"):
            cents = await get_credit_balance_cents(db, telegram_user_id)
            await telegram_api.send_message(
                chat_id,
                f"Store credit: ${cents / 100:.2f}",
                reply_markup={
                    "inline_keyboard": [
                        [{"text": "Open Dashboard", "web_app": {"url": settings.mini_app_url}}]
                    ]
                },
            )

        elif text.startswith("/buy_credit") or text.startswith("/buy"):
            await send_stars_invoice(
                db, chat_id=chat_id, telegram_user_id=telegram_user_id, sku="credit_1_usd"
            )

        elif text.startswith("/buy_hour"):
            await send_stars_invoice(
                db, chat_id=chat_id, telegram_user_id=telegram_user_id, sku="hour_voucher_1h"
            )

        successful_payment = message.get("successful_payment")
        if successful_payment:
            order_id = uuid.UUID(successful_payment["invoice_payload"])

            await fulfill_order_from_payment(
                db,
                order_id=order_id,
                provider=PROVIDER_TELEGRAM_STARS,
                external_ref=successful_payment["telegram_payment_charge_id"],
                amount=int(successful_payment["total_amount"]),
                currency=successful_payment["currency"],
                raw_payload=successful_payment,
            )

            with contextlib.suppress(RuntimeError):
                await telegram_api.send_message(
                    chat_id, "Payment confirmed. Fulfillment started ✅"
                )
            await db.commit()

    if callback_query:
        query_id = callback_query["id"]
        data = callback_query.get("data", "")
        from_user = callback_query.get("from") or {}
        telegram_user_id = int(from_user["id"])
        message_obj = callback_query.get("message") or {}
        chat_id = message_obj.get("chat", {}).get("id")

        await _tg("answerCallbackQuery", {"callback_query_id": query_id})

        if data.startswith("stars:") and chat_id:
            sku = data.removeprefix("stars:")
            await send_stars_invoice(
                db, chat_id=chat_id, telegram_user_id=telegram_user_id, sku=sku
            )

    if pre_checkout_query:
        query_id = pre_checkout_query["id"]
        telegram_user_id = int(pre_checkout_query["from"]["id"])
        order_id = uuid.UUID(pre_checkout_query["invoice_payload"])

        ok = await validate_order_for_checkout(
            db,
            order_id=order_id,
            telegram_user_id=telegram_user_id,
            amount=int(pre_checkout_query["total_amount"]),
            currency=pre_checkout_query["currency"],
        )

        payload: dict[str, Any] = {"pre_checkout_query_id": query_id, "ok": ok}
        if not ok:
            payload["error_message"] = "Invalid or expired order."

        await _tg("answerPreCheckoutQuery", payload)

    return {"ok": True}
