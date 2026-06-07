from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.wallet import UserWallet


async def get_wallet(db: AsyncSession, telegram_user_id: int) -> UserWallet | None:
    return await db.scalar(
        select(UserWallet).where(UserWallet.telegram_user_id == telegram_user_id)
    )


async def upsert_wallet(
    db: AsyncSession,
    *,
    telegram_user_id: int,
    ton_address: str,
    wallet_app: str | None = None,
) -> UserWallet:
    stmt = pg_insert(UserWallet.__table__).values(
        telegram_user_id=telegram_user_id,
        ton_address=ton_address,
        wallet_app=wallet_app,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["telegram_user_id"],
        set_={
            "ton_address": stmt.excluded.ton_address,
            "wallet_app": stmt.excluded.wallet_app,
            "updated_at": func.now(),
        },
    )

    await db.execute(stmt)
    await db.commit()

    wallet = await get_wallet(db, telegram_user_id)
    if not wallet:
        raise RuntimeError("Failed to persist wallet")
    return wallet
