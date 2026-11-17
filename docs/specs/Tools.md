# Development and Product Tools

## 1. Recommended toolset

| Purpose | Recommended tool | Alternatives/notes |
|---|---|---|
| Source control | Git + GitHub | Require branch protection and reviews |
| Web framework | Next.js + TypeScript | Keep app typed and componentized |
| Styling/components | Tailwind CSS + shadcn/ui | Validate accessibility and maintain tokens |
| API | FastAPI | Python domain services |
| Data processing | Pandas / Polars / OpenPyXL | Choose parser based on file profile and tests |
| Database | PostgreSQL | Managed service or container locally |
| Migrations | Alembic | Required for schema changes |
| Queue | Redis + Celery or equivalent | Select and document one queue stack |
| Storage | S3-compatible private object store | Use private buckets and short-lived access |
| Identity | Supabase Auth or Clerk | Choose one after evaluation |
| Payments | Razorpay for India; Stripe where available and appropriate | Verify current terms, availability and tax handling |
| AI | Provider abstraction for an LLM | Optional; keep core processing provider-independent |
| Charts | Recharts | Pair charts with accessible tables |
| Testing | Pytest, Vitest, Playwright | Add contract and security tests |
| Lint/format | Ruff, ESLint, Prettier | Enforce in CI |
| Observability | Sentry plus structured logs/metrics | Redact financial payloads |
| API docs | FastAPI OpenAPI | Publish only non-secret schemas |
| Design | Figma | Components and design tokens |

## 2. Tool selection rules

- Prefer managed services for critical infrastructure when the team cannot operate them safely.
- Evaluate total cost, data location, exportability, lock-in, support and security before selecting a provider.
- Do not add duplicate libraries for the same responsibility.
- Pin versions and update dependencies regularly.
- Review licenses and vulnerability advisories.
- Use free tiers only when their limits and production suitability are understood.

## 3. Environments

- Local: synthetic data and local services.
- Test: deterministic fixtures and isolated database.
- Staging: anonymized data, restricted credentials and production-like infrastructure.
- Production: customer data, least privilege, backups and approved access only.

## 4. Secrets

Use `.env` locally and a secret manager in hosted environments. `.env.example` contains names and safe placeholders only. Rotate leaked credentials immediately and review Git history if a secret is committed.

## 5. AI development tools

AI coding tools may read project docs and modify code in a branch. They must follow Agents.md and Rules.md. Give them synthetic data and minimum repository permissions. Require human review for financial logic, authentication, security, migrations and deployment.
