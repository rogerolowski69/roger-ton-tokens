from __future__ import annotations

from fastapi import Header, HTTPException

from apps.api.services.telegram_auth import (
    TelegramUser,
    parse_telegram_user,
    validate_webapp_init_data,
)


def _extract_init_data(
    x_telegram_init_data: str | None,
    authorization: str | None,
) -> str:
    if x_telegram_init_data:
        return x_telegram_init_data
    if authorization and authorization.startswith("tma "):
        return authorization[4:]
    raise HTTPException(status_code=401, detail="Missing Telegram initData")


async def require_telegram_user(
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    authorization: str | None = Header(default=None),
) -> TelegramUser:
    init_data = _extract_init_data(x_telegram_init_data, authorization)
    verified = validate_webapp_init_data(init_data)
    return parse_telegram_user(verified)
