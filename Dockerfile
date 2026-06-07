FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY apps ./apps
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh

RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev \
    && chmod +x ./scripts/entrypoint.sh

ENV RUN_MIGRATIONS_ON_STARTUP=true \
    SEED_PRODUCTS_ON_STARTUP=true \
    LOG_JSON=true \
    APP_DEBUG=false

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f "http://127.0.0.1:${PORT:-8080}/health" || exit 1

CMD ["./scripts/entrypoint.sh"]
