from __future__ import annotations

import os

os.environ["RUN_MIGRATIONS_ON_STARTUP"] = "false"
os.environ["SEED_PRODUCTS_ON_STARTUP"] = "false"
os.environ["APP_DEBUG"] = "false"

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
