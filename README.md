# Roger TON Tokens

Telegram Mini App + ledger-backed store credit API + Acton TIME jetton contracts.

[![CI](https://github.com/YOUR_ORG/roger-ton-tokens/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_ORG/roger-ton-tokens/actions/workflows/ci.yml)

## Stack

| Layer | Tech |
|-------|------|
| Mini App | React + Vite + TonConnect |
| API | FastAPI + SQLAlchemy + Alembic |
| Database | PostgreSQL |
| Contracts | Acton 1.1 / Tolk (TEP-74 jetton) |

## Project tree

```
.
├─ Acton.toml              # Smart contracts (repo root)
├─ railway.toml            # Railway API service config
├─ Dockerfile              # Production API image
├─ contracts/              # JettonMinter + JettonWallet
├─ tests/                  # Acton contract tests (53)
├─ apps/api/               # FastAPI backend
├─ frontend/               # React TWA (frontend/railway.toml)
├─ api-tests/              # Pytest
├─ alembic/                # Postgres migrations
├─ scripts/                # Deploy, webhook, Railway helpers
└─ justfile                # All dev commands
```

## Local development

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env

just install
just migrate
just build-contracts
just test-contracts
just restart          # postgres + API + frontend
just smoke
```

| Command | Purpose |
|---------|---------|
| `just dev` | API `:3001` + frontend `:5173` |
| `just build-contracts` | Compile Tolk contracts |
| `just test-contracts` | Acton emulation tests |
| `just test-api` | Pytest |
| `just lint` | Ruff |
| `just webhook` | Register Telegram webhook (local/prod) |
| `just repl` | IPython + DB |

Contract docs: [`contracts/README.md`](contracts/README.md)

## Deploy on Railway

Two services from the **same GitHub repo** (monorepo):

### 1. PostgreSQL

1. Create a Railway project → **Add PostgreSQL**
2. Copy `DATABASE_URL` (Railway provides `postgres://…` — the API normalizes it automatically)

### 2. API service

1. **New Service** → Deploy from GitHub repo
2. **Root Directory:** leave empty (repo root)
3. Railway reads [`railway.toml`](railway.toml) + [`Dockerfile`](Dockerfile)
4. Set variables from [`.env.railway.example`](.env.railway.example):

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference) |
| `BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_WEBHOOK_SECRET` | Random string (32+ chars) |
| `API_BASE_URL` | `https://your-api.up.railway.app` |
| `MINI_APP_URL` | `https://your-frontend.up.railway.app` |
| `LOG_JSON` | `true` |

5. Deploy → health check hits `/health`
6. Generate domain in Railway → update `API_BASE_URL`

### 3. Frontend service

1. **New Service** → same repo
2. **Root Directory:** `frontend`
3. Uses [`frontend/railway.toml`](frontend/railway.toml) + Nixpacks
4. Build variables:

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | Your API public URL |
| `VITE_MINI_APP_URL` | Your frontend public URL |

5. Generate domain → set `MINI_APP_URL` on **API** service too (CORS)

### 4. Post-deploy

```bash
# With Railway CLI linked, or run locally with production .env:
just railway-check
just railway-webhook    # registers bot webhook + menu button
```

In [@BotFather](https://t.me/BotFather): set Mini App URL to your frontend domain.

### Checklist

- [ ] Postgres linked to API
- [ ] API `/health` returns `{"ok":true}`
- [ ] Frontend loads over HTTPS
- [ ] `API_BASE_URL` and `MINI_APP_URL` match Railway domains
- [ ] Webhook registered (`just webhook`)
- [ ] TonConnect manifest generated at build (`npm run prebuild`)

## GitHub

```bash
git init
git add .
git commit -m "Initial commit"
gh repo create roger-ton-tokens --public --source=. --push
```

CI runs on every PR: API lint/test, Acton contracts, frontend build, Docker build (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

Connect Railway to GitHub for auto-deploy on `main`.

## API endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Railway health check |
| `GET /ready` | DB connectivity |
| `GET /api/auth/me` | Telegram initData auth |
| `POST /api/webhooks/telegram` | Bot + Stars payments |
| `POST /api/checkout/*` | Checkout flows |

With `APP_DEBUG=true`: `GET /debug/*`

## Ledger rule

Never update `credit_accounts.balance_cents` outside the same transaction as a `credit_ledger` insert.

## License

MIT — see [LICENSE](LICENSE)
