from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.order import (
    FULFILL_MINT_JETTON,
    FULFILL_STORE_CREDIT,
    FULFILL_TIME_VOUCHER,
    ORDER_FULFILLED,
    ORDER_FULFILLING,
    ORDER_PAID,
    ORDER_PENDING,
    PROVIDER_STORE_CREDIT,
    PROVIDER_STRIPE,
    PROVIDER_TELEGRAM_STARS,
    PROVIDER_TON_WALLET,
    CreditAccount,
    CreditLedger,
    Order,
    PaymentAttempt,
    Product,
    TokenGrant,
)


class OrderError(Exception):
    pass


class InsufficientCredit(OrderError):
    pass


def now_utc() -> datetime:
    return datetime.now(UTC)


async def seed_products(db: AsyncSession) -> None:
    rows = [
        {
            "id": uuid.uuid4(),
            "sku": "credit_1_usd",
            "name": "$1 Website Credit",
            "fulfillment_kind": FULFILL_STORE_CREDIT,
            "price_cents": 100,
            "stars_amount": 50,
            "ton_amount_nano": 350_000_000,
            "credit_cents": 100,
            "service_minutes": 0,
            "active": True,
        },
        {
            "id": uuid.uuid4(),
            "sku": "hour_voucher_1h",
            "name": "1 Hour Time Voucher",
            "fulfillment_kind": FULFILL_TIME_VOUCHER,
            "price_cents": 100,
            "stars_amount": 50,
            "ton_amount_nano": 350_000_000,
            "credit_cents": 0,
            "service_minutes": 60,
            "active": True,
        },
    ]

    stmt = pg_insert(Product.__table__).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["sku"],
        set_={
            "name": stmt.excluded.name,
            "fulfillment_kind": stmt.excluded.fulfillment_kind,
            "price_cents": stmt.excluded.price_cents,
            "stars_amount": stmt.excluded.stars_amount,
            "ton_amount_nano": stmt.excluded.ton_amount_nano,
            "credit_cents": stmt.excluded.credit_cents,
            "service_minutes": stmt.excluded.service_minutes,
            "active": stmt.excluded.active,
        },
    )

    await db.execute(stmt)
    await db.commit()


def _expected_for_provider(product: Product, provider: str) -> tuple[int, str]:
    if provider == PROVIDER_TELEGRAM_STARS:
        if product.stars_amount is None:
            raise OrderError("Product is not available via Telegram Stars")
        return int(product.stars_amount), "XTR"

    if provider == PROVIDER_STORE_CREDIT:
        return int(product.price_cents), "CREDIT_CENTS"

    if provider == PROVIDER_STRIPE:
        return int(product.price_cents), "USD_CENTS"

    if provider == PROVIDER_TON_WALLET:
        if product.ton_amount_nano is None:
            raise OrderError("Product is not available via TON wallet")
        return int(product.ton_amount_nano), "TON_NANO"

    raise OrderError(f"Unsupported provider: {provider}")


async def create_order_for_sku(
    db: AsyncSession,
    *,
    telegram_user_id: int,
    sku: str,
    provider: str,
) -> Order:
    async with db.begin():
        product = await db.scalar(
            select(Product).where(Product.sku == sku, Product.active.is_(True))
        )

        if not product:
            raise OrderError(f"Product not found or inactive: {sku}")

        expected_amount, expected_currency = _expected_for_provider(product, provider)

        order = Order(
            id=uuid.uuid4(),
            telegram_user_id=telegram_user_id,
            product_id=product.id,
            sku=product.sku,
            provider=provider,
            status=ORDER_PENDING,
            expected_amount=expected_amount,
            expected_currency=expected_currency,
        )

        db.add(order)
        await db.flush()

        return order


async def validate_order_for_checkout(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    telegram_user_id: int,
    amount: int,
    currency: str,
) -> bool:
    order = await db.scalar(
        select(Order).where(
            Order.id == order_id,
            Order.telegram_user_id == telegram_user_id,
            Order.provider == PROVIDER_TELEGRAM_STARS,
            Order.status == ORDER_PENDING,
        )
    )

    if not order:
        return False

    return int(order.expected_amount) == int(amount) and order.expected_currency == currency


async def _ensure_credit_account_locked(
    db: AsyncSession,
    *,
    telegram_user_id: int,
) -> CreditAccount:
    stmt = pg_insert(CreditAccount.__table__).values(
        telegram_user_id=telegram_user_id,
        balance_cents=0,
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["telegram_user_id"])

    await db.execute(stmt)

    account = await db.scalar(
        select(CreditAccount)
        .where(CreditAccount.telegram_user_id == telegram_user_id)
        .with_for_update()
    )

    if not account:
        raise OrderError("Could not create or lock credit account")

    return account


async def _append_credit_ledger_locked(
    db: AsyncSession,
    *,
    telegram_user_id: int,
    order_id: uuid.UUID | None,
    direction: str,
    amount_cents: int,
    reason: str,
    external_ref: str,
) -> None:
    if amount_cents <= 0:
        raise OrderError("Ledger amount must be positive")

    account = await _ensure_credit_account_locked(
        db,
        telegram_user_id=telegram_user_id,
    )

    if direction == "credit":
        new_balance = account.balance_cents + amount_cents
    elif direction == "debit":
        new_balance = account.balance_cents - amount_cents
    else:
        raise OrderError(f"Invalid ledger direction: {direction}")

    if new_balance < 0:
        raise InsufficientCredit("Insufficient store credit")

    account.balance_cents = new_balance

    db.add(
        CreditLedger(
            id=uuid.uuid4(),
            telegram_user_id=telegram_user_id,
            order_id=order_id,
            direction=direction,
            amount_cents=amount_cents,
            balance_after_cents=new_balance,
            reason=reason,
            external_ref=external_ref,
        )
    )


async def _apply_fulfillment_locked(
    db: AsyncSession,
    *,
    order: Order,
    product: Product,
) -> None:
    if product.fulfillment_kind == FULFILL_STORE_CREDIT:
        await _append_credit_ledger_locked(
            db,
            telegram_user_id=order.telegram_user_id,
            order_id=order.id,
            direction="credit",
            amount_cents=product.credit_cents,
            reason=f"purchase:{product.sku}",
            external_ref=f"credit:{order.id}",
        )

        order.status = ORDER_FULFILLED
        order.fulfilled_at = now_utc()
        return

    if product.fulfillment_kind == FULFILL_TIME_VOUCHER:
        grant = TokenGrant(
            id=uuid.uuid4(),
            order_id=order.id,
            telegram_user_id=order.telegram_user_id,
            sku=product.sku,
            token_kind="time_voucher",
            service_minutes=product.service_minutes,
            mint_status="pending",
            redeem_status="unused",
        )

        db.add(grant)
        order.status = ORDER_FULFILLING
        return

    if product.fulfillment_kind == FULFILL_MINT_JETTON:
        grant = TokenGrant(
            id=uuid.uuid4(),
            order_id=order.id,
            telegram_user_id=order.telegram_user_id,
            sku=product.sku,
            token_kind="jetton",
            service_minutes=0,
            mint_status="pending",
            redeem_status="unused",
        )

        db.add(grant)
        order.status = ORDER_FULFILLING
        return

    raise OrderError(f"Unsupported fulfillment kind: {product.fulfillment_kind}")


async def fulfill_order_from_payment(
    db: AsyncSession,
    *,
    order_id: uuid.UUID,
    provider: str,
    external_ref: str,
    amount: int | Decimal,
    currency: str,
    raw_payload: dict[str, Any],
) -> None:
    async with db.begin():
        payment_insert = pg_insert(PaymentAttempt.__table__).values(
            id=uuid.uuid4(),
            order_id=order_id,
            provider=provider,
            external_ref=external_ref,
            amount=int(amount),
            currency=currency,
            status="confirmed",
            raw_payload=raw_payload,
        )

        payment_insert = payment_insert.on_conflict_do_nothing(
            index_elements=["provider", "external_ref"]
        ).returning(PaymentAttempt.id)

        result = await db.execute(payment_insert)
        inserted_payment_id = result.scalar_one_or_none()

        if inserted_payment_id is None:
            existing_payment = await db.scalar(
                select(PaymentAttempt).where(
                    PaymentAttempt.provider == provider,
                    PaymentAttempt.external_ref == external_ref,
                )
            )

            if not existing_payment:
                raise OrderError("Payment conflict but existing payment not found")

            if existing_payment.order_id != order_id:
                raise OrderError("Payment reference belongs to another order")

        order = await db.scalar(
            select(Order).where(Order.id == order_id).with_for_update()
        )

        if not order:
            raise OrderError("Order not found")

        if order.status in {ORDER_PAID, ORDER_FULFILLING, ORDER_FULFILLED}:
            return

        if order.status != ORDER_PENDING:
            raise OrderError(f"Order is not payable: {order.status}")

        if order.provider != provider:
            raise OrderError("Provider mismatch")

        if order.expected_currency != currency:
            raise OrderError("Currency mismatch")

        if int(amount) < int(order.expected_amount):
            raise OrderError("Insufficient payment amount")

        product = await db.scalar(select(Product).where(Product.id == order.product_id))

        if not product:
            raise OrderError("Product not found")

        order.status = ORDER_PAID
        order.paid_at = now_utc()

        await _apply_fulfillment_locked(db, order=order, product=product)


async def pay_order_with_store_credit(
    db: AsyncSession,
    *,
    telegram_user_id: int,
    sku: str,
) -> Order:
    async with db.begin():
        product = await db.scalar(
            select(Product).where(Product.sku == sku, Product.active.is_(True))
        )

        if not product:
            raise OrderError(f"Product not found or inactive: {sku}")

        price_cents = int(product.price_cents)

        order = Order(
            id=uuid.uuid4(),
            telegram_user_id=telegram_user_id,
            product_id=product.id,
            sku=product.sku,
            provider=PROVIDER_STORE_CREDIT,
            status=ORDER_PENDING,
            expected_amount=price_cents,
            expected_currency="CREDIT_CENTS",
        )

        db.add(order)
        await db.flush()

        await _append_credit_ledger_locked(
            db,
            telegram_user_id=telegram_user_id,
            order_id=order.id,
            direction="debit",
            amount_cents=price_cents,
            reason=f"spend:{product.sku}",
            external_ref=f"debit:{order.id}",
        )

        db.add(
            PaymentAttempt(
                id=uuid.uuid4(),
                order_id=order.id,
                provider=PROVIDER_STORE_CREDIT,
                external_ref=f"store_credit:{order.id}",
                amount=price_cents,
                currency="CREDIT_CENTS",
                status="confirmed",
                raw_payload={"source": "credit_ledger"},
            )
        )

        order.status = ORDER_PAID
        order.paid_at = now_utc()

        await _apply_fulfillment_locked(db, order=order, product=product)

        return order


async def get_credit_balance_cents(
    db: AsyncSession,
    telegram_user_id: int,
) -> int:
    account = await db.scalar(
        select(CreditAccount).where(CreditAccount.telegram_user_id == telegram_user_id)
    )
    return int(account.balance_cents) if account else 0
