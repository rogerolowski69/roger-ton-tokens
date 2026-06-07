from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.db import Base


class UserWallet(Base):
    __tablename__ = "user_wallets"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ton_address: Mapped[str] = mapped_column(String(120), nullable=False)
    wallet_app: Mapped[str | None] = mapped_column(String(64), nullable=True)

    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
