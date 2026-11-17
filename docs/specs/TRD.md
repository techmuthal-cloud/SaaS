# Technical Requirements Document (TRD)

## 1. Purpose

This document defines the technology and quality requirements for implementing SellerFlow AI. It complements the PRD: the PRD says what the product should do; this document defines technical constraints and operational expectations.

## 2. Proposed stack

| Layer | Recommended option | Notes |
|---|---|---|
| Web frontend | Next.js + TypeScript | Responsive web application |
| UI | Tailwind CSS + accessible component library | Tokens and shared components |
| API | Python FastAPI | REST API and OpenAPI schema |
| Worker | Python worker with Celery or equivalent | Long-running imports and exports |
| Queue/cache | Redis | Job queue and short-lived cache; not source of truth |
| Database | PostgreSQL | Transactional source of truth |
| Object storage | S3-compatible private bucket | Original files and generated exports |
| Identity | Supabase Auth or Clerk | Select one before implementation; avoid dual identity systems |
| AI | Provider abstraction | Optional language model for classification and grounded explanations |
| Observability | Structured logs, metrics, error tracking | Never log raw sensitive spreadsheet rows by default |
| Deployment | Containerized API/worker plus managed web hosting | Choose environment based on operational capability |

## 3. Functional technical requirements

- All financial data belongs to a workspace/tenant.
- Every persisted business record must carry a tenant/workspace key or be reachable through a tenant-scoped parent.
- Imports must be idempotent using file checksum, source identifiers and import scope.
- Raw uploaded files must remain immutable after ingestion.
- Normalized records must retain source file, sheet, row number and import provenance.
- Matching logic must be deterministic and versioned.
- Every financial amount must include currency and defined decimal precision.
- Use decimal arithmetic for money; do not use binary floating-point for financial totals.
- Long-running work must execute asynchronously and report progress.
- API operations must validate tenant membership and permissions server-side.
- Exports must be reproducible from the same data and calculation version.

## 4. Non-functional requirements

Initial targets are engineering goals to validate under realistic workloads, not contractual SLAs.

| Area | Initial target |
|---|---|
| Web availability | Target 99.5% monthly during MVP, excluding announced maintenance |
| API latency | p95 under 500 ms for common metadata/list endpoints under expected MVP load |
| Upload responsiveness | Return an import/job ID quickly; file parsing happens asynchronously |
| Recoverability | Database backups and documented restore test before paid launch |
| Security | TLS, encrypted managed storage, least privilege, tenant isolation |
| Accessibility | Target WCAG 2.2 AA for core flows |
| Browser support | Current stable Chrome, Edge, Firefox and Safari; validate actual browser matrix |
| Localization | Currency and date formatting by explicit workspace settings; avoid hardcoded locale assumptions |
| Auditability | Versioned mapping and matching rules, source references, actor and timestamp for critical actions |

## 5. Data processing requirements

1. Validate extension, MIME type, file signature, archive contents and file size.
2. Store original file in private object storage.
3. Create an import record and enqueue processing job.
4. Scan and parse file in an isolated worker with resource limits.
5. Detect report type and schema version.
6. Ask user to confirm ambiguous mapping.
7. Normalize rows into canonical staging tables.
8. Validate required fields and report row-level errors.
9. Promote valid rows transactionally or mark the import partially processed with explicit counts.
10. Run matching using a versioned ruleset.
11. Persist results and source references.
12. Generate exports asynchronously.

## 6. Financial calculation requirements

- Use `Decimal` in Python and `NUMERIC`/`DECIMAL` in PostgreSQL.
- Define rounding rules per currency/report type; never silently round intermediate calculations.
- Distinguish gross sales, discounts, taxes, fees, refunds, settlement and bank deposit.
- Define sign conventions for credits and debits per adapter.
- Keep raw marketplace values and normalized values separately.
- Record calculation version and input snapshot/identifiers.
- Missing cost must be `unknown`/`not provided`, not zero by default.
- Every metric must disclose included and excluded cost components.

## 7. API requirements

- REST JSON API under `/api/v1`.
- OpenAPI generated from FastAPI schemas.
- Consistent error envelope and validation errors.
- Pagination for list endpoints.
- Idempotency key for sensitive create/submit operations where retries may duplicate work.
- Rate limits at identity and tenant levels.
- Request IDs propagated to workers and logs.

## 8. Operational requirements

- Separate web, API, worker and scheduler processes.
- Health endpoints for liveness and readiness.
- Queue depth and failed-job metrics.
- Dead-letter handling for repeated failures.
- Database migrations run in deployment pipeline with backups and rollback plan.
- Secrets stored in environment/secret manager, never in repository.
- Disaster recovery and incident contact ownership defined before production launch.

## 9. Technical decisions to record

Maintain an Architecture Decision Record (ADR) for:
- Identity provider selection.
- Marketplace first adapter and import strategy.
- Object storage provider and retention.
- Queue/worker choice.
- AI provider and data minimization strategy.
- Payment provider and tax/invoice treatment.
- Hosting and backup strategy.
