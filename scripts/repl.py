#!/usr/bin/env python3
"""Interactive shell with app settings, DB engine, and models loaded."""
from __future__ import annotations

import asyncio

from IPython import start_ipython

import apps.api.models  # noqa: F401
from apps.api.config import settings
from apps.api.db import SessionLocal, engine
from apps.api.logging_config import configure_logging
from apps.api.models.order import CreditAccount, Order, Product
from apps.api.models.wallet import UserWallet


async def _open_session():
    return SessionLocal()


def main() -> None:
    configure_logging()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    start_ipython(
        argv=[],
        user_ns={
            "settings": settings,
            "engine": engine,
            "SessionLocal": SessionLocal,
            "db": _open_session,
            "Product": Product,
            "Order": Order,
            "CreditAccount": CreditAccount,
            "UserWallet": UserWallet,
            "asyncio": asyncio,
        },
        banner1="""
Roger TON Token REPL — settings, engine, SessionLocal, db(), models
""",
        display_banner=False,
    )
    loop.close()


if __name__ == "__main__":
    main()
