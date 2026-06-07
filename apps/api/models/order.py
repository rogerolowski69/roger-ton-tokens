from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.db import Base

ORDER_PENDING = "pending"
ORDER_PAID = "paid"
ORDER_FULFILLING = "fulfilling"
ORDER_FULFILLED = "fulfilled"
ORDER_FAILED = "failed"
ORDER_EXPIRED = "expired"

PROVIDER_TELEGRAM_STARS = "telegram_stars"
PROVIDER_STORE_CREDIT = "store_credit"
PROVIDER_STRIPE = "stripe"
PROVIDER_TON_WALLET = "ton_wallet"

FULFILL_STORE_CREDIT = "store_credit"
FULFILL_TIME_VOUCHER = "time_voucher"
FULFILL_MINT_JETTON = "mint_jetton"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))

    fulfillment_kind: Mapped[str] = mapped_column(String(40))

    price_cents: Mapped[int] = mapped_column(Integer)
    stars_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ton_amount_nano: Mapped[int | None] = mapped_column(Numeric(78, 0), nullable=True)
    credit_cents: Mapped[int] = mapped_column(Integer, default=0)
    service_minutes: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        index=True,
    )

    sku: Mapped[str] = mapped_column(String(80), index=True)

    provider: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(40), default=ORDER_PENDING, index=True)

    expected_amount: Mapped[int] = mapped_column(Numeric(78, 0))
    expected_currency: Mapped[str] = mapped_column(String(32))

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    paid_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fulfilled_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        index=True,
    )

    provider: Mapped[str] = mapped_column(String(40), index=True)
    external_ref: Mapped[str] = mapped_column(String(220))

    amount: Mapped[int] = mapped_column(Numeric(78, 0))
    currency: Mapped[str] = mapped_column(String(32))

    status: Mapped[str] = mapped_column(String(40), default="confirmed")
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    confirmed_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("provider", "external_ref", name="uq_payment_provider_ref"),
    )


class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)

    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=True,
        index=True,
    )

    direction: Mapped[str] = mapped_column(String(10))
    amount_cents: Mapped[int] = mapped_column(Integer)
    balance_after_cents: Mapped[int] = mapped_column(Integer)

    reason: Mapped[str] = mapped_column(String(120))
    external_ref: Mapped[str] = mapped_column(String(220), unique=True)

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("direction IN ('credit', 'debit')", name="ck_credit_direction"),
        CheckConstraint("amount_cents > 0", name="ck_credit_amount_positive"),
    )


class TokenGrant(Base):
    __tablename__ = "token_grants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        unique=True,
        index=True,
    )

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    sku: Mapped[str] = mapped_column(String(80))

    token_kind: Mapped[str] = mapped_column(String(40), default="time_voucher")
    service_minutes: Mapped[int] = mapped_column(Integer, default=0)

    recipient_wallet: Mapped[str | None] = mapped_column(String(120), nullable=True)

    mint_status: Mapped[str] = mapped_column(String(40), default="pending")
    token_ref: Mapped[str | None] = mapped_column(String(220), nullable=True)
    mint_tx_hash: Mapped[str | None] = mapped_column(String(220), nullable=True)

    redeem_status: Mapped[str] = mapped_column(String(40), default="unused")

    scheduled_start: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_end: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    minted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    redeemed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
