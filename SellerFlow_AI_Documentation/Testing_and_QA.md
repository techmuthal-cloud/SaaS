# Testing and Quality Assurance

## 1. QA objectives

Protect financial correctness, tenant isolation, file safety and user trust. A visually correct dashboard is not sufficient if the underlying totals or source traceability are wrong.

## 2. Test pyramid

### Unit tests
- Parsers and type conversions.
- Decimal calculations and rounding.
- Matching rules.
- Sign conventions.
- Permission functions.
- File validation.
- Export escaping.

### Integration tests
- API + database.
- Upload + object storage.
- Queue + worker.
- Import + normalization.
- Reconciliation + source lineage.
- Export generation and authorized download.

### Contract tests
- Frontend/API schema agreement.
- Identity provider claims.
- Marketplace adapter sample schema.
- Webhook signatures where applicable.

### End-to-end tests
- Signup, workspace creation and first import.
- Mapping confirmation.
- Reconciliation and discrepancy review.
- Profit input and export.
- Role restrictions and tenant isolation.

## 3. Financial correctness test suite

Build an independent “golden dataset” with expected outputs verified outside the application. Include:
- Exact one-to-one settlement.
- Partial payout.
- Multiple settlement lines for one order.
- One settlement covering multiple orders.
- Refund and return.
- Fee debit and fee reversal.
- Cancellation.
- Duplicate rows.
- Missing order ID.
- Ambiguous candidate match.
- Currency mismatch.
- Different timezone/date boundary.
- Negative and zero values.
- Rounding and precision edge cases.
- Late settlement outside the order period.

Acceptance: calculated values must match expected outputs to the documented currency precision. Ambiguous cases must remain ambiguous rather than being forced into a match.

## 4. File safety tests

- Wrong extension/content signature.
- Oversized file.
- Huge row count.
- Malformed CSV encoding.
- XLSX with excessive sheets/cells.
- ZIP expansion bomb patterns.
- Formula payloads.
- Empty and duplicate headers.
- Hidden sheets and unexpected workbook content.
- Invalid dates and numeric formats.

## 5. Security tests

- User A cannot access User B's workspace, file, export or source row.
- Viewer cannot upload or alter data.
- Expired/revoked token rejected.
- IDOR tests for all resource endpoints.
- Upload URL cannot be reused outside its intended scope.
- Export URL expires and cannot access another tenant's artifact.
- Rate limits apply.
- Audit events are created for privileged actions.

## 6. Performance tests

Set workload targets after collecting real sample file sizes. Test:
- Large CSV parse time and memory.
- Concurrent imports across tenants.
- Reconciliation query performance.
- Export generation.
- Queue backlog and retry behaviour.
- Dashboard queries for large workspaces.

## 7. QA release checklist

- [ ] P0 acceptance criteria pass.
- [ ] Independent financial fixtures pass.
- [ ] No critical/high tenant isolation issue.
- [ ] File validation/resource limits pass.
- [ ] API and frontend contract tests pass.
- [ ] Migration tested on staging snapshot.
- [ ] Backup restore procedure verified.
- [ ] Error and retry behaviour tested.
- [ ] Accessibility checks completed.
- [ ] Privacy and retention behaviours tested.
- [ ] Product copy matches shipped capability.
- [ ] Monitoring and rollback path ready.

## 8. Defect severity

- P0/Critical: cross-tenant data exposure, wrong financial output at scale, credential compromise, irreversible data loss. Block release.
- P1/High: core import/reconciliation broken, incorrect important totals, privilege escalation. Block affected release.
- P2/Medium: limited feature defect with workaround and no integrity/security impact.
- P3/Low: cosmetic issue or minor usability improvement.
