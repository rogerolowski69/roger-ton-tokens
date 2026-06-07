from __future__ import annotations

from pathlib import Path

from alembic.config import Config

from alembic import command


def sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return database_url


def alembic_config(project_root: Path | None = None) -> Config:
    root = project_root or Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    return config


def upgrade_head(project_root: Path | None = None) -> None:
    command.upgrade(alembic_config(project_root), "head")
