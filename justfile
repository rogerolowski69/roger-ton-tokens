#!/usr/bin/env bash
# Roger TON Tokens — API + Acton contracts at repo root

set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
    @just --list

# --- Install ---

install:
    uv sync --group dev
    cd frontend && npm install
    acton up

install-acton:
    acton up

# --- Python API ---

dev:
    #!/usr/bin/env bash
    set -euo pipefail
    just dev-api &
    just dev-frontend &
    wait

dev-api:
    uv run uvicorn apps.api.main:app --reload --port 3001 --log-level debug

debug-api:
    uv run python -m debugpy --listen 5678 --wait-for-client -m uvicorn apps.api.main:app --reload --port 3001

dev-frontend:
    cd frontend && npm run dev

restart:
    #!/usr/bin/env bash
    set -euo pipefail
    pkill -f "uvicorn apps.api.main" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    docker compose down 2>/dev/null || true
    docker compose up -d postgres
    echo "Waiting for Postgres..."
    for i in $(seq 1 30); do
      docker compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1 && break
      sleep 1
    done
    uv run alembic upgrade head
    uv run uvicorn apps.api.main:app --reload --port 3001 &
    sleep 2
    cd frontend && npm run dev &
    echo ""
    echo "  API:      http://localhost:3001"
    echo "  Frontend: http://localhost:5173"
    echo "  Docs:     http://localhost:3001/docs"
    wait

migrate:
    uv run alembic upgrade head

migrate-stamp:
    uv run alembic stamp head

seed:
    PYTHONPATH=. uv run python scripts/seed_products.py

webhook:
    uv run python scripts/set_telegram_webhook.py

smoke:
    PYTHONPATH=. uv run python scripts/smoke_test_local.py

repl:
    PYTHONPATH=. uv run python scripts/repl.py

lint:
    uv run ruff check .
    uv run ruff format --check .

format:
    uv run ruff format .
    uv run ruff check --fix .

test-api:
    uv run pytest -v api-tests

docker-up:
    docker compose up -d --build

docker-down:
    docker compose down

logs:
    docker compose logs -f

build-frontend:
    cd frontend && npm run build

# --- Acton (contracts at repo root) ---

doctor:
    acton doctor
    acton --version

build-contracts:
    acton build

test-contracts:
    acton test

fmt-contracts:
    acton fmt

check-contracts:
    acton check

deploy-emulation:
    acton run deploy-emulation

deploy-testnet:
    acton run deploy-testnet

jetton-info:
    acton run jetton-info

jetton-mint:
    acton run jetton-mint

buy-time:
    acton run buy-time

ci: build-contracts fmt-contracts check-contracts test-contracts lint test-api

# --- Railway ---

railway-check:
    PYTHONPATH=. uv run python scripts/railway_check_env.py

railway-webhook:
    PYTHONPATH=. uv run python scripts/set_telegram_webhook.py

docker-build:
    docker build -t roger-ton-api:local .

clean:
    rm -rf frontend/dist frontend/node_modules build gen .acton/cache
    find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true

purge:
    just clean
    docker compose down -v 2>/dev/null || true
