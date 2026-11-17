## Description
<!-- Provide a clear summary of the changes and the problem solved. -->

## Financial & Accounting Invariants Checklist
Please verify the following financial requirements before requesting review:
- [ ] **No Float Math**: All financial and monetary calculations use `decimal.Decimal` and database `NUMERIC(18,2)`.
- [ ] **Like-for-Like Fee Audit**: Rate card fee checks compare expected fee components with corresponding actual deduction lines (not gross sales vs. net payout).
- [ ] **Discrepancy Integrity**: Discrepancies represent investigation exceptions, never added or subtracted as cash.
- [ ] **Provenance Maintained**: Every normalized transaction line retains its source row and import ID reference.

## Security & Tenant Isolation Checklist
- [ ] **Tenant Isolation**: Protected endpoints verify that the authenticated user has membership in the requested workspace (`verify_tenant_access`).
- [ ] **Upload Safety**: File paths use random UUIDs; no user-supplied filenames in file paths.
- [ ] **Export Sanitization**: CSV and Excel text exports pass through `sanitize_for_spreadsheet` to neutralize formula injection (`=`, `+`, `-`, `@`).
- [ ] **Zero Hardcoded Secrets**: Secrets and API keys are stored in environment variables.

## Testing & Quality Gates
- [ ] Backend tests passing (`python -m pytest tests/ -v`).
- [ ] Frontend builds without errors (`npm run build` in `apps/web`).
- [ ] New automated unit/integration tests added for new behavior.
