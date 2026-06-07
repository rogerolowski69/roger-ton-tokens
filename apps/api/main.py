from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import settings
from apps.api.db import SessionLocal, get_db
from apps.api.db_migrate import upgrade_head
from apps.api.logging_config import configure_logging, get_logger
from apps.api.middleware.request_log import RequestLogMiddleware
from apps.api.routers.auth import router as auth_router
from apps.api.routers.checkout import router as checkout_router
from apps.api.routers.debug import router as debug_router
from apps.api.routers.telegram_bot import router as telegram_router
from apps.api.routers.wallet import router as wallet_router
from apps.api.services.orders import seed_products

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", app_debug=settings.app_debug, log_level=settings.log_level)

    if settings.run_migrations_on_startup:
        await asyncio.to_thread(upgrade_head)

    if settings.seed_products_on_startup:
        async with SessionLocal() as db:
            await seed_products(db)

    yield

    log.info("shutdown")


app = FastAPI(
    title="Roger TON Token API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(checkout_router)
app.include_router(telegram_router)

if settings.app_debug:
    app.include_router(debug_router)
    log.warning("debug_routes_enabled", prefix="/debug")


@app.get("/ready")
async def ready(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        log.exception("ready_db_check_failed")
        raise HTTPException(status_code=503, detail="database unavailable") from exc

    return {"ok": True}


@app.get("/health")
async def health(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """Railway / load-balancer alias for /ready."""
    return await ready(db)
