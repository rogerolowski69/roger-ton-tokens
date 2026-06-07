from __future__ import annotations

import time
from typing import Any

from alembic.script import ScriptDirectory
from fastapi import APIRouter, Depends
from fastapi.routing import APIRoute
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.db import SessionLocal, engine, get_db
from apps.api.db_migrate import alembic_config
from apps.api.models.order import CreditAccount, Order, Product
from apps.api.models.wallet import UserWallet

router = APIRouter(prefix="/debug", tags=["debug"])

_SENSITIVE = frozenset({"bot_token", "telegram_webhook_secret", "database_url"})


def _redact_settings() -> dict[str, Any]:
    data = settings.model_dump()
    for key in _SENSITIVE:
        if key in data and data[key]:
            value = str(data[key])
            data[key] = f"***{value[-4:]}" if len(value) > 4 else "***"
    return data


def _migration_head() -> str | None:
    script = ScriptDirectory.from_config(alembic_config())
    return script.get_current_head()


@router.get("/health")
async def debug_health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    started = time.perf_counter()
    await db.execute(text("SELECT 1"))
    db_latency_ms = round((time.perf_counter() - started) * 1000, 2)

    pool = engine.sync_engine.pool
    return {
        "ok": True,
        "db_latency_ms": db_latency_ms,
        "migration_head": _migration_head(),
        "pool": {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        },
    }


@router.get("/config")
async def debug_config() -> dict[str, Any]:
    return _redact_settings()


@router.get("/stats")
async def debug_stats(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    counts = {}
    for label, model in (
        ("products", Product),
        ("orders", Order),
        ("credit_accounts", CreditAccount),
        ("user_wallets", UserWallet),
    ):
        result = await db.scalar(select(func.count()).select_from(model))
        counts[label] = int(result or 0)
    return counts


@router.get("/routes")
async def debug_routes() -> list[dict[str, str]]:
    from apps.api.main import app

    routes: list[dict[str, str]] = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(
                {
                    "path": route.path,
                    "methods": ",".join(sorted(route.methods or [])),
                    "name": route.name,
                }
            )
    return sorted(routes, key=lambda item: item["path"])


@router.post("/seed")
async def debug_seed() -> dict[str, str]:
    from apps.api.services.orders import seed_products

    async with SessionLocal() as db:
        await seed_products(db)
        await db.commit()
    return {"status": "seeded"}
