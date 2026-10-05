# chengzi

Django + PostgreSQL API with a [Preact](https://preactjs.com) (Vite) frontend.

Same-origin by default: Django + WhiteNoise serve the built SPA and `/api` together so session cookies work without CORS.

## Stack

| Layer | Tech |
| --- | --- |
| API | Django 6 + Django REST Framework |
| Static / SPA | WhiteNoise serving `frontend/dist` |
| DB | PostgreSQL |
| UI | Preact + TypeScript + Vite |

```
chengzi/
├── api/              # Django app
├── config/           # Django project settings
├── manage.py
├── frontend/         # Preact + Vite
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.12+ and [uv](https://github.com/astral-sh/uv)
- Node.js `^20.19.0` or `>=22.12.0`
- PostgreSQL (local Postgres.app, Homebrew, or Docker)

## Quick start

### 1. Environment

```bash
cp .env.example .env
```

Defaults expect local databases `chengzi` (dev) and `chengzi_test` (pytest), user/password `chengzi`.

### 2. Database

**local Postgres**

```bash
createuser -s chengzi 2>/dev/null || true
createdb -O chengzi chengzi 2>/dev/null || true
createdb -O chengzi chengzi_test 2>/dev/null || true
psql -d postgres -c "ALTER USER chengzi WITH PASSWORD 'chengzi' CREATEDB;"
```

Pytest uses `chengzi_test` (`POSTGRES_TEST_DB`) and reuses it across runs (`--reuse-db`). Recreate the schema with `uv run pytest --create-db` when migrations change.

### 3. Build frontend + run Django (same origin)

```bash
cd frontend && npm install && npm run build && cd ..
uv sync
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) — UI and API share one origin.

- Health: `GET /api/health/`

### 4. Frontend HMR (optional, local only)

Keep Django running on `:8000`, then:

```bash
cd frontend
npm run dev
```

Vite on [http://localhost:5173](http://localhost:5173) proxies `/api` to Django. Use this for day-to-day UI work; use the same-origin Django server when testing session cookies.

## Useful commands

```bash
# Tests
uv run pytest

# Lint / format
uv run ruff check .
uv run ruff format .

# Django shell
uv run python manage.py shell

# Create a superuser
uv run python manage.py createsuperuser

# Rebuild SPA after frontend changes (for Django-served mode)
cd frontend && npm run build
```
