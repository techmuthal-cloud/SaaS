# API Specification

## 1. Conventions

- Base path: `/api/v1`
- Transport: HTTPS
- Format: JSON, except file upload/download endpoints
- Authentication: bearer access token from selected identity provider
- IDs: UUID strings
- Time: ISO 8601 UTC timestamps
- Money: decimal string plus currency code; do not serialize money as imprecise binary float
- Pagination: `limit` and opaque `cursor`
- Idempotency: support `Idempotency-Key` on upload-intent, processing and payment-sensitive operations where retry duplication is possible

## 2. Standard response patterns

Success:

```json
{
  "data": {},
  "meta": { "request_id": "req_example" }
}
```

Error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The uploaded report is missing a required column.",
    "details": [{ "field": "order_id", "issue": "required column not mapped" }]
  },
  "meta": { "request_id": "req_example" }
}
```

Never include stack traces, secrets, raw access tokens or other tenants' data in error responses.

## 3. Endpoint catalogue

### Identity and workspace
- `GET /me` – current user and available workspaces.
- `POST /workspaces` – create workspace.
- `GET /workspaces` – list accessible workspaces.
- `GET /workspaces/{workspace_id}` – workspace details.
- `PATCH /workspaces/{workspace_id}` – update permitted settings.
- `GET /workspaces/{workspace_id}/members` – list members.
- `POST /workspaces/{workspace_id}/invitations` – invite member.
- `PATCH /workspaces/{workspace_id}/members/{member_id}` – change role/status.

### Businesses and stores
- `POST /workspaces/{workspace_id}/businesses`
- `GET /workspaces/{workspace_id}/businesses`
- `POST /workspaces/{workspace_id}/stores`
- `GET /workspaces/{workspace_id}/stores`
- `PATCH /workspaces/{workspace_id}/stores/{store_id}`
- `GET /workspaces/{workspace_id}/integrations`

### Imports
- `POST /workspaces/{workspace_id}/imports` – create import and issue upload URL or receive multipart file.
- `GET /workspaces/{workspace_id}/imports` – list imports.
- `GET /workspaces/{workspace_id}/imports/{import_id}` – import status and summary.
- `POST /workspaces/{workspace_id}/imports/{import_id}/confirm-mapping` – confirm mapping.
- `POST /workspaces/{workspace_id}/imports/{import_id}/retry` – retry eligible failed job.
- `DELETE /workspaces/{workspace_id}/imports/{import_id}` – request deletion if allowed.

Example import metadata:

```json
{
  "store_id": "00000000-0000-0000-0000-000000000001",
  "file_name": "settlement-report.csv",
  "report_type_hint": "settlement",
  "period_start": "2026-10-01",
  "period_end": "2026-10-31"
}
```

### Reconciliation
- `POST /workspaces/{workspace_id}/reconciliation-runs` – create run for selected imports/period.
- `GET /workspaces/{workspace_id}/reconciliation-runs` – list runs.
- `GET /workspaces/{workspace_id}/reconciliation-runs/{run_id}` – summary/status.
- `GET /workspaces/{workspace_id}/reconciliation-runs/{run_id}/matches` – paginated matches.
- `GET /workspaces/{workspace_id}/reconciliation-runs/{run_id}/discrepancies` – exception list.

### Discrepancies
- `GET /workspaces/{workspace_id}/discrepancies/{discrepancy_id}` – detail with source references.
- `PATCH /workspaces/{workspace_id}/discrepancies/{discrepancy_id}` – update review status/assignment.
- `POST /workspaces/{workspace_id}/discrepancies/{discrepancy_id}/notes` – add note.
- `GET /workspaces/{workspace_id}/discrepancies/{discrepancy_id}/history` – audit history.

### Profitability
- `GET /workspaces/{workspace_id}/profitability/summary`
- `GET /workspaces/{workspace_id}/profitability/products`
- `GET /workspaces/{workspace_id}/profitability/products/{product_id}`
- `POST /workspaces/{workspace_id}/products/{product_id}/costs`
- `PATCH /workspaces/{workspace_id}/product-costs/{cost_id}`

### Reports and exports
- `POST /workspaces/{workspace_id}/exports` – request report generation.
- `GET /workspaces/{workspace_id}/exports` – list exports.
- `GET /workspaces/{workspace_id}/exports/{export_id}` – export status.
- `POST /workspaces/{workspace_id}/exports/{export_id}/download-url` – create short-lived authorized URL.

### Notifications and audit
- `GET /workspaces/{workspace_id}/notifications`
- `PATCH /workspaces/{workspace_id}/notifications/{notification_id}`
- `GET /workspaces/{workspace_id}/audit-events` – permission-restricted.

## 4. Asynchronous job pattern

Long-running requests return `202 Accepted`:

```json
{
  "data": {
    "job_id": "00000000-0000-0000-0000-000000000002",
    "resource_id": "00000000-0000-0000-0000-000000000003",
    "status": "queued",
    "status_url": "/api/v1/workspaces/.../imports/..."
  },
  "meta": { "request_id": "req_example" }
}
```

The client polls the resource status with exponential backoff or uses a supported notification channel later.

## 5. Authorization rules

- `viewer`: read permitted workspace data.
- `analyst`: upload and run permitted analyses; no member/billing/security administration.
- `accountant`: financial review and report export; scope can be restricted to assigned businesses/clients.
- `admin`: workspace operations and member management except ownership transfer/billing owner actions as defined.
- `owner`: full workspace authority.

The backend is authoritative. Hiding buttons in the frontend is not authorization.

## 6. Filtering and sorting

Whitelist sortable fields. Validate date ranges and maximum query windows. For transaction searches, require workspace and preferably store/period filters for large datasets. Never accept arbitrary SQL/order expressions.

## 7. Versioning and deprecation

- Maintain `/api/v1` compatibility during MVP.
- Breaking changes require a new API version or a documented migration window.
- Generate OpenAPI and typed frontend clients from the same schemas where practical.
- Keep marketplace-specific raw fields inside adapter payloads; expose stable canonical fields in shared API contracts.
