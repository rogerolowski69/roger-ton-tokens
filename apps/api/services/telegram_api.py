"""Telegram Bot API wrapper — httpx only."""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from apps.api.config import settings

log = structlog.get_logger(__name__)
BASE = f"https://api.telegram.org/bot{settings.bot_token}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
    reraise=True,
)
async def tg(method: str, payload: dict[str, Any]) -> Any:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{BASE}/{method}", json=payload)
        data = r.json()

    if not data.get("ok"):
        log.warning("telegram_api_error", method=method, response=data)
        raise RuntimeError(f"Telegram API error: {data}")

    return data["result"]


async def create_invoice_link(
    *,
    title: str,
    description: str,
    payload: str,
    currency: str,
    prices: list[dict[str, Any]],
) -> str:
    return await tg(
        "createInvoiceLink",
        {
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": "",
            "currency": currency,
            "prices": prices,
        },
    )


async def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> Any:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await tg("sendMessage", payload)


async def send_invoice(
    *,
    chat_id: int,
    title: str,
    description: str,
    payload: str,
    currency: str,
    prices: list[dict[str, Any]],
) -> Any:
    return await tg(
        "sendInvoice",
        {
            "chat_id": chat_id,
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": "",
            "currency": currency,
            "prices": prices,
        },
    )
