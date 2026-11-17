# Product and Engineering Rules

## 1. Product rules

1. Do not advertise a marketplace integration until it passes the Integration Readiness Checklist.
2. Do not claim a discrepancy is a recovered amount or confirmed marketplace error without evidence.
3. Do not call estimated profitability “actual profit” when material cost components are missing.
4. Do not present a tax calculation as filing-ready or legally compliant without qualified review.
5. Free demo data must be synthetic and visibly labelled.
6. Pricing, usage limits, cancellation and refund policies must be public and understandable.

## 2. Financial data rules

1. Use decimal types for money.
2. Preserve raw source values and normalized values.
3. Keep source file, sheet and row provenance.
4. Version every mapping and matching ruleset.
5. Record currency and sign convention.
6. Treat unknown as unknown, not zero.
7. Do not silently drop invalid rows; report them.
8. Do not force ambiguous matches.
9. Reconciliation runs are immutable snapshots; corrections create new runs/versions.
10. Any manual override requires actor, reason, timestamp and audit event.

## 3. AI rules

- AI is assistive, never the financial source of truth.
- AI must not write directly to normalized ledger or settlement tables.
- All answers about customer data must retrieve only data the current user is authorized to access.
- AI-generated explanations must reference computed facts and identify uncertainty.
- Imported files and retrieved documents are untrusted content, not instructions.
- Do not send sensitive data to model providers unless data minimization, user disclosure/consent and provider review are completed.
- Do not fabricate missing fees, transactions, mappings or marketplace behaviour.

## 4. Security rules

- Every API resource lookup must include authorization and tenant scope.
- Never trust a workspace ID, role or owner flag supplied only by the client.
- Never commit secrets.
- Never make uploaded objects public by default.
- Never log access/refresh tokens or full sensitive rows.
- Apply least privilege to workers and services.
- Require explicit approval for production data mutations.

## 5. Engineering rules

- Type-check and lint code.
- Keep domain logic separate from HTTP handlers and UI components.
- Write tests with each behaviour change.
- Add migration and rollback notes for schema changes.
- Keep APIs backward-compatible within a version where practical.
- Use idempotent background jobs.
- Handle retries and partial failures explicitly.
- Update docs when public behaviour changes.

## 6. UX rules

- Every data page has loading, empty, partial, error and success states.
- Status cannot rely on colour alone.
- Every discrepancy links to evidence.
- Every financial metric discloses period, currency and known exclusions.
- Destructive operations require confirmation.
- Tables support keyboard use and accessible labels.

## 7. Release rules

Block release for critical tenant-isolation, financial correctness, credential exposure or data-loss defects. Feature flags must default to off for unverified connectors. Production deployment requires a rollback plan and verified backups.
