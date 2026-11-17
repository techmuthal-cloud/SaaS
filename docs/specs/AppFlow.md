# Application Flows

## 1. First-time user flow

```mermaid
flowchart TD
  A[Marketing website] --> B[Sign up / Sign in]
  B --> C[Verify identity]
  C --> D[Create workspace]
  D --> E[Create business profile]
  E --> F[Add marketplace store]
  F --> G[Choose import method]
  G --> H[Upload sample or real report]
  H --> I[Validate and detect format]
  I --> J{Mapping clear?}
  J -- No --> K[Confirm column mapping]
  J -- Yes --> L[Normalize records]
  K --> L
  L --> M[Run reconciliation]
  M --> N[Review summary and discrepancies]
  N --> O[View profitability / export]
```

## 2. Upload/import state flow

```mermaid
stateDiagram-v2
  [*] --> Uploaded
  Uploaded --> Validating
  Validating --> NeedsMapping
  Validating --> Queued: schema recognized
  Validating --> Failed: invalid file
  NeedsMapping --> Queued: user confirms mapping
  Queued --> Processing
  Processing --> Completed
  Processing --> CompletedWithWarnings
  Processing --> Failed
  Failed --> Queued: eligible retry
  Completed --> [*]
  CompletedWithWarnings --> [*]
```

## 3. Reconciliation review flow

```mermaid
flowchart TD
  A[Choose store and period] --> B[Select processed imports]
  B --> C[Run versioned matching rules]
  C --> D[Generate matches and exceptions]
  D --> E[View summary]
  E --> F{Any exceptions?}
  F -- No --> G[Export reconciliation]
  F -- Yes --> H[Open discrepancy]
  H --> I[Inspect source records and rule]
  I --> J[Add note / assign / mark for follow-up]
  J --> K[Audit event recorded]
  K --> E
```

## 4. Role-dependent flows

- Viewer: dashboard, reports and permitted transaction details only.
- Analyst: upload, map, process and review reconciliation.
- Accountant: assigned client/business scope and financial exports.
- Admin: workspace and member management.
- Owner: all workspace features including billing and security settings.

## 5. Error and recovery flows

- Invalid file: show reason and allowed file requirements; no processing job.
- Unknown schema: route to mapping review; do not guess silently.
- Partial data: show missing source type and partial result label.
- Worker failure: preserve job and import state; retry only if idempotent.
- Ambiguous match: open review queue.
- Expired integration token: request reconnect; stop automatic sync.
- Export failure: keep export request with safe error code and retry option.

## 6. User notification events

- Import completed.
- Import completed with warnings.
- Import failed.
- Mapping needs confirmation.
- Reconciliation run completed.
- New discrepancy requires review.
- Export ready or failed.
- Integration needs reconnect.

Notifications must not expose sensitive transaction details in email subject lines or push previews.
