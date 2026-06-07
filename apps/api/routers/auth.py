from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from apps.api.deps.auth import require_telegram_user
from apps.api.services.telegram_auth import TelegramUser

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthMeResponse(BaseModel):
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    is_premium: bool
    photo_url: str | None


@router.get("/me", response_model=AuthMeResponse)
async def auth_me(user: TelegramUser = Depends(require_telegram_user)) -> AuthMeResponse:
    return AuthMeResponse(
        telegram_user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_premium=user.is_premium,
        photo_url=user.photo_url,
    )
