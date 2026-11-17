# Project Implementation Plan

## 1. Delivery strategy

Implement SellerFlow AI in incremental, demonstrable releases. Prioritize a reliable manual-import reconciliation workflow before automated marketplace connections, advanced AI or multi-client functionality.

## 2. Phase 0 – Discovery and feasibility

Deliverables:
- 10–15 seller/accountant interviews.
- Observed month-end workflow notes.
- Sample reports obtained with permission and anonymized where needed.
- First marketplace decision.
- Report field dictionary and sign convention.
- Manual reconciliation baseline for test cases.
- Paid-pilot willingness-to-pay evidence.

Exit criteria:
- A recurring painful workflow is identified.
- At least one report set can be understood end-to-end.
- Expected results can be independently calculated.
- Initial pilot users agree to test the workflow.

## 3. Phase 1 – Foundation

Workstreams:
- Repository, CI, linting, formatting and test framework.
- Next.js shell, design tokens and navigation.
- FastAPI app, configuration and OpenAPI.
- PostgreSQL schema and Alembic migrations.
- Managed authentication and workspace membership.
- Private object storage and upload security.
- Audit logging and request IDs.

Exit criteria:
- User can register, create workspace and access only their workspace.
- CI passes and staging deployment works.

## 4. Phase 2 – Import pipeline

Workstreams:
- Upload intent and private storage.
- Import status state machine.
- CSV/XLSX parsing with row/size/time limits.
- Report type detection.
- Column mapping UI and saved mapping versions.
- Canonical model and source provenance.
- Import error report.

Exit criteria:
- Representative fixture files parse deterministically.
- Row counts and source references are auditable.
- Invalid files fail safely.

## 5. Phase 3 – Reconciliation MVP

Workstreams:
- Canonical order and settlement records.
- Versioned matching rules.
- Exact/partial/ambiguous/unmatched states.
- Reconciliation summary and discrepancy detail.
- Source-record traceability.
- Notes and review status.
- Independent financial test fixtures.

Exit criteria:
- Expected totals match independently verified results.
- Ambiguous records are not auto-confirmed.
- No cross-tenant access is possible in automated tests.

## 6. Phase 4 – Profitability and exports

Workstreams:
- Product/SKU identity mapping.
- Cost inputs with effective dates.
- Fee and return allocation rules.
- Profit coverage indicators.
- CSV/XLSX export with formula-injection protection.
- Export history and expiry.

Exit criteria:
- Calculation detail shows included/missing costs.
- UI/export amounts match.
- Recalculation is versioned and reproducible.

## 7. Phase 5 – Pilot and hardening

Workstreams:
- Guided onboarding.
- Support ticket path.
- Usage analytics.
- Performance and security testing.
- Backup restore test.
- Privacy, terms and data retention review.
- Customer feedback and workflow observation.

Exit criteria:
- Pilot users complete the target workflow without developer intervention or with documented support needs.
- No unresolved critical security or financial correctness defects.
- Clear go/no-go decision for paid launch.

## 8. Phase 6 – Expansion

Prioritize based on measured demand:
1. Next marketplace adapter.
2. Multiple stores.
3. Accountant workspace.
4. Advertising cost imports.
5. Official API automation.
6. AI assistant grounded in reconciled data.
7. Bank/accounting integrations.

## 9. Suggested issue labels

`P0`, `P1`, `P2`, `frontend`, `backend`, `data-pipeline`, `reconciliation`, `security`, `privacy`, `qa`, `docs`, `blocked`, `needs-product-decision`.

## 10. Delivery controls

- Work in small pull requests.
- Link each PR to user story and acceptance criteria.
- Require code review for financial logic and access control.
- Run migrations and tests in staging before production.
- Feature-flag unverified adapters.
- Keep a release changelog and rollback plan.
