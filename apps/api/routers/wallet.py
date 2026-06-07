from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps.auth import require_telegram_user
from apps.api.services.telegram_auth import TelegramUser
from apps.api.services.wallet import get_wallet, upsert_wallet

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


class WalletConnectRequest(BaseModel):
    ton_address: str = Field(min_length=48, max_length=120)
    wallet_app: str | None = Field(default=None, max_length=64)


class WalletResponse(BaseModel):
    connected: bool
    ton_address: str | None = None
    wallet_app: str | None = None


@router.get("", response_model=WalletResponse)
async def wallet_status(
    user: TelegramUser = Depends(require_telegram_user),
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    wallet = await get_wallet(db, user.id)
    if not wallet:
        return WalletResponse(connected=False)
    return WalletResponse(
        connected=True,
        ton_address=wallet.ton_address,
        wallet_app=wallet.wallet_app,
    )


@router.post("/connect", response_model=WalletResponse)
async def wallet_connect(
    body: WalletConnectRequest,
    user: TelegramUser = Depends(require_telegram_user),
    db: AsyncSession = Depends(get_db),
) -> WalletResponse:
    wallet = await upsert_wallet(
        db,
        telegram_user_id=user.id,
        ton_address=body.ton_address.strip(),
        wallet_app=body.wallet_app,
    )
    return WalletResponse(
        connected=True,
        ton_address=wallet.ton_address,
        wallet_app=wallet.wallet_app,
    )
