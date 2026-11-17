# AI Coding Agents and Agent Responsibilities

## 1. Purpose

This file defines safe, scoped responsibilities for AI coding agents working on SellerFlow AI. Agents assist engineering; they do not own product decisions, financial correctness sign-off or production authorization.

## 2. Agent roles

### Product Analyst Agent
- Converts validated user problems into user stories.
- Maintains scope, assumptions and acceptance criteria.
- Flags unvalidated competitor claims and product assumptions.
- Cannot silently expand MVP scope.

### UX Agent
- Produces journeys, wireframes, content and component states.
- Covers empty, loading, error, partial and success states.
- Checks accessibility and responsive behaviour.
- Must not invent supported integrations or financial claims.

### Frontend Agent
- Implements Next.js UI and typed API integration.
- Uses shared design tokens and accessible components.
- Treats client state as untrusted.
- Does not implement financial source-of-truth calculations in the browser.

### Backend Agent
- Implements FastAPI domain modules and authorization.
- Enforces workspace/tenant scope on every query.
- Uses transactions, idempotency and structured errors.
- Does not trust frontend role claims.

### Data Processing Agent
- Implements parser, validation, canonical normalization and provenance.
- Provides fixtures and deterministic outputs.
- Uses Decimal for money.
- Never silently drops rows or guesses ambiguous fields.

### Reconciliation Agent
- Implements versioned matching strategies.
- Separates exact, partial, ambiguous and unmatched states.
- Emits evidence and source-record references.
- Does not optimize for match rate at the expense of correctness.

### AI/LLM Agent
- Builds column-mapping suggestions and grounded explanations.
- Uses tenant-scoped retrieval and data minimization.
- Cannot write to financial ledgers or determine final totals.
- Clearly labels uncertainty.

### QA Agent
- Creates unit, integration, contract, security and regression tests.
- Uses synthetic or authorized anonymized fixtures.
- Verifies totals against independent expected results.
- Blocks release on critical data isolation or financial correctness failures.

### DevOps Agent
- Maintains containers, CI/CD, environment configuration and monitoring.
- Uses least-privilege credentials.
- Requires approval for production deployment and destructive infrastructure operations.

## 3. Universal agent rules

1. Read relevant docs before modifying code.
2. Inspect repository conventions before creating files.
3. State assumptions when requirements are incomplete.
4. Do not claim a feature is complete without tests.
5. Keep changes focused and reviewable.
6. Do not modify production data or secrets.
7. Do not add a dependency without explaining why.
8. Never weaken authorization or validation to make a test pass.
9. Never fabricate marketplace API behaviour; verify current official documentation.
10. Update docs and tests alongside behaviour changes.

## 4. Handoff format

Every agent task should conclude with:
- Summary of changes.
- Files changed.
- Design/architecture decisions.
- Tests executed and results.
- Known limitations.
- Security/privacy impact.
- Follow-up tasks or blockers.

## 5. Human approval gates

Human approval is required for:
- Product scope and marketplace selection.
- Financial matching rule changes.
- AI provider/data-sharing changes.
- Production deployment.
- Database migrations that can delete or rewrite data.
- Marketplace OAuth scope expansion.
- Customer-visible billing, refunds or external messages.
