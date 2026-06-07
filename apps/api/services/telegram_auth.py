from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from time import time
from typing import Any
from urllib.parse import parse_qsl

from fastapi import HTTPException

from apps.api.config import settings


@dataclass(frozen=True)
class TelegramUser:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    is_premium: bool
    photo_url: str | None


def validate_webapp_init_data(init_data: str, max_age_seconds: int = 86400) -> dict[str, Any]:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing initData hash")

    auth_date_raw = pairs.get("auth_date")
    if not auth_date_raw:
        raise HTTPException(status_code=401, detail="Missing auth_date")

    auth_date = int(auth_date_raw)
    if time() - auth_date > max_age_seconds:
        raise HTTPException(status_code=401, detail="Expired initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(
        b"WebAppData",
        settings.bot_token.encode(),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid initData")

    user_raw = pairs.get("user")
    user = json.loads(user_raw) if user_raw else {}

    if not user.get("id"):
        raise HTTPException(status_code=401, detail="Missing Telegram user")

    return {"user": user, "raw": pairs}


def parse_telegram_user(verified: dict[str, Any]) -> TelegramUser:
    user = verified["user"]
    return TelegramUser(
        id=int(user["id"]),
        username=user.get("username"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        language_code=user.get("language_code"),
        is_premium=bool(user.get("is_premium")),
        photo_url=user.get("photo_url"),
    )
