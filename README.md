# chengzi

Django + PostgreSQL API with a [Preact](https://preactjs.com) (Vite) frontend.

## Stack

| Layer | Tech |
| --- | --- |
| API | Django 6 + Django REST Framework |
| DB | PostgreSQL |
| UI | Preact + TypeScript + Vite |

```
chengzi/
├── backend/          # Django project (`config`) + `api` app
├── frontend/         # Preact + Vite
├── docker-compose.yml
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.12+ and [uv](https://github.com/astral-sh/uv)
- Node.js 20+
- PostgreSQL (local Postgres.app, Homebrew, or Docker)

## Quick start

### 1. Environment

```bash
cp .env.example .env
```

Defaults expect a local database named `chengzi` with user/password `chengzi`.

### 2. Database

**Option A — Docker**

```bash
docker compose up -d
```

**Option B — local Postgres** (already set up on this machine if you followed the scaffold)

```bash
# create role + database if needed
createuser -s chengzi 2>/dev/null || true
createdb -O chengzi chengzi 2>/dev/null || true
psql -d postgres -c "ALTER USER chengzi WITH PASSWORD 'chengzi';"
```

### 3. Backend

```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

API base: [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/)

- Health: `GET /api/health/`
- Notes CRUD: `/api/notes/`

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: [http://localhost:5173](http://localhost:5173)

Vite proxies `/api` to Django (`http://127.0.0.1:8000`) during development.

## Useful commands

```bash
# Django shell
cd backend && uv run python manage.py shell

# Create a superuser
cd backend && uv run python manage.py createsuperuser

# Production-ish frontend build
cd frontend && npm run build
```
