from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.db import get_db
from apps.api.deps.auth import require_telegram_user
from apps.api.models.order import PROVIDER_TELEGRAM_STARS, PROVIDER_TON_WALLET
from apps.api.services.orders import (
    InsufficientCredit,
    OrderError,
    create_order_for_sku,
    fulfill_order_from_payment,
    get_credit_balance_cents,
    pay_order_with_store_credit,
)
from apps.api.services.telegram_api import send_invoice as _unused  # noqa: F401
from apps.api.services.telegram_auth import TelegramUser

router = APIRouter(prefix="/api/checkout", tags=["checkout"])

# Re-export telegram API helpers used by checkout
from apps.api.services import telegram_api  # noqa: E402


class SkuRequest(BaseModel):
    sku: str


class StarsInvoiceResponse(BaseModel):
    order_id: str
    invoice_link: str


class StoreCreditPayResponse(BaseModel):
    ok: str
    order_id: str
    status: str


class BalanceResponse(BaseModel):
    telegram_user_id: int
    balance_cents: int
    balance_usd: str


class TonPrepareResponse(BaseModel):
    order_id: str
    merchant_address: str
    amount_nano: str
    comment: str


class TonConfirmRequest(BaseModel):
    order_id: str
    tx_hash: str = Field(min_length=16, max_length=128)


class TonConfirmResponse(BaseModel):
    order_id: str
    status: str


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user: TelegramUser = Depends(require_telegram_user),
    db: AsyncSession = Depends(get_db),
) -> BalanceResponse:
    cents = await get_credit_balance_cents(db, user.id)
    return BalanceResponse(
        telegram_user_id=user.id,
        balance_cents=cents,
        balance_usd=f"{cents / 100:.2f}",
    )


@router.post("/stars/invoice-link", response_model=StarsInvoiceResponse)
async def create_stars_invoice_link(
    body: SkuRequest,
    user: TelegramUser = Depends(require_telegram_user),
    db: AsyncSession = Depends(get_db),
) -> StarsInvoiceResponse:
    order = await create_order_for_sku(
        db,
        telegram_user_id=user.id,
        sku=body.sku,
        provider=PROVIDER_TELEGRAM_STARS,
    )

    invoice_link = await telegram_api.create_invoice_link(
        title="Roger Token Purchase",
        description=f"Purchase: {body.sku}",
        payload=str(order.id),
        currency="XTR",
        prices=[{"label": body.sku, "amount": int(order.expected_amount)}],
    )

    return StarsInvoiceResponse(order_id=str(order.id), invoice_link=invoice_link)


@router.post("/store-credit/pay", response_model=StoreCreditPayResponse)
async def pay_with_store_credit(
    body: SkuRequest,
    user: TelegramUser = Depends(require_telegram_user),
    db: AsyncSession = Depends(get_db),
) -> StoreCreditPayResponse:
    try:
        order = await pay_order_with_store_credit(
            db,
            telegram_user_id=user.id,
            sku=body.sku,
        )
    except InsufficientCredit as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StoreCreditPayResponse(
        ok="true",
        order_id=str(order.id),
        status=order.status,
    )


@router.post("/ton/prepare", response_model=TonPrepareResponse)
async def ton_prepare(
    body: SkuRequest,
    user: TelegramUser = Depends(require_telegram_user),
    db: AsyncSession = Depends(get_db),
) -> TonPrepareResponse:
    if not settings.merchant_ton_wallet:
        raise HTTPException(status_code=503, detail="TON payments not configured")

    order = await create_order_for_sku(
        db,
        telegram_user_id=user.id,
        sku=body.sku,
        provider=PROVIDER_TON_WALLET,
    )

    return TonPrepareResponse(
        order_id=str(order.id),
        merchant_address=settings.merchant_ton_wallet,
        amount_nano=str(int(order.expected_amount)),
        comment=str(order.id),
    )


@router.post("/ton/confirm", response_model=TonConfirmResponse)
async def ton_confirm(
    body: TonConfirmRequest,
    user: TelegramUser = Depends(require_telegram_user),
    db: AsyncSession = Depends(get_db),
) -> TonConfirmResponse:
    try:
        order_id = uuid.UUID(body.order_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid order_id") from exc

    from sqlalchemy import select

    from apps.api.models.order import Order

    order = await db.scalar(select(Order).where(Order.id == order_id))
    if not order or order.telegram_user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.provider != PROVIDER_TON_WALLET:
        raise HTTPException(status_code=400, detail="Not a TON order")

    try:
        await fulfill_order_from_payment(
            db,
            order_id=order_id,
            provider=PROVIDER_TON_WALLET,
            external_ref=body.tx_hash,
            amount=int(order.expected_amount),
            currency="TON_NANO",
            raw_payload={"tx_hash": body.tx_hash, "confirmed_by": "client"},
        )
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await db.refresh(order)
    return TonConfirmResponse(order_id=str(order.id), status=order.status)
