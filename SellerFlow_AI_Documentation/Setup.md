# Local Development Setup

## 1. Prerequisites

Install supported stable versions of:
- Git
- Node.js LTS and npm/pnpm
- Python 3.11+ (pin the exact supported version in `.python-version`)
- Docker Desktop or compatible container runtime
- PostgreSQL (or use Docker Compose)
- Redis (or use Docker Compose)

Exact versions should be pinned by the implementation repository and CI configuration.

## 2. Clone and configure

```bash
git clone <YOUR_REPOSITORY_URL> sellerflow-ai
cd sellerflow-ai
cp .env.example .env
```

Do not commit `.env`. Use test credentials and synthetic data locally.

## 3. Example environment variables

```dotenv
APP_ENV=local
WEB_BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
DATABASE_URL=postgresql+psycopg://sellerflow:sellerflow@localhost:5432/sellerflow
REDIS_URL=redis://localhost:6379/0
OBJECT_STORAGE_ENDPOINT=http://localhost:9000
OBJECT_STORAGE_BUCKET=sellerflow-local
OBJECT_STORAGE_ACCESS_KEY=change-me
OBJECT_STORAGE_SECRET_KEY=change-me
AUTH_ISSUER_URL=
AUTH_AUDIENCE=
AUTH_JWKS_URL=
AI_PROVIDER=disabled
AI_API_KEY=
LOG_LEVEL=INFO
```

Values are examples only. Use the selected identity and storage provider's documented configuration. Do not reuse production keys.

## 4. Start infrastructure

A Docker Compose file should provide PostgreSQL, Redis and optional local S3-compatible storage. Start it with:

```bash
docker compose up -d
```

## 5. Backend setup

```bash
cd apps/api
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Run the worker in a separate terminal using the command defined by the repository (for example, a Celery worker command). Do not assume a queue implementation until selected in the codebase.

## 6. Frontend setup

```bash
cd apps/web
pnpm install
pnpm dev
```

Open `http://localhost:3000`.

## 7. Test setup

```bash
# Backend
pytest
ruff check .
ruff format --check .

# Frontend
pnpm lint
pnpm typecheck
pnpm test
```

Actual scripts may differ; keep this file aligned with `package.json`, `pyproject.toml` and CI.

## 8. Local sample data

- Use only synthetic or explicitly authorized anonymized reports.
- Keep fixtures in `tests/fixtures/` with a README describing their origin and expected output.
- Never commit real seller financial reports or marketplace credentials.

## 9. Common setup problems

- Database connection refused: confirm container health, port mapping and `DATABASE_URL`.
- Migration failure: inspect current revision and run migrations in order; do not delete the database to hide a migration issue.
- Auth issuer mismatch: compare issuer/audience with the identity provider environment.
- Worker not processing: confirm Redis, queue name, task import path and worker logs.
- Upload denied: verify private bucket, CORS, upload policy and allowed file size.
