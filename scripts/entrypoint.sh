#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-3001}"

if [[ "${RUN_MIGRATIONS_ON_STARTUP:-true}" == "true" ]]; then
  echo "Running database migrations..."
  uv run alembic upgrade head
fi

echo "Starting API on 0.0.0.0:${PORT}"
exec uv run uvicorn apps.api.main:app --host 0.0.0.0 --port "${PORT}" "$@"
