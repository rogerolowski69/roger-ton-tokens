from __future__ import annotations

import asyncio

from apps.api.db import SessionLocal
from apps.api.services.orders import seed_products


async def main() -> None:
    async with SessionLocal() as db:
        await seed_products(db)
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
