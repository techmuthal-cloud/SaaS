# Database Design

## 1. Database principles

- PostgreSQL is the system of record.
- Use UUID primary keys.
- Use `NUMERIC(20, 6)` or a narrower documented precision for monetary quantities; use Python `Decimal` in application code.
- Persist currency as ISO 4217 code where applicable.
- Store timestamps in UTC; retain source timezone/offset when the report provides it.
- All business-owned records must be tenant-scoped.
- Keep raw source references and normalized values separate.
- Prefer soft deletion for user-facing records where auditability requires it; apply retention/deletion policies to file content and personal data.

## 2. Core ER model

```text
users (identity provider subject)
  |< workspace_members >| workspaces
                            |
                            |< businesses
                            |< stores > marketplace_connections
                            |< imports > source_files
                            |< report_mappings
                            |< orders
                            |< settlement_transactions
                            |< reconciliation_runs
                            |< reconciliation_matches > source_records
                            |< discrepancies
                            |< product_costs > products
                            |< exports
                            |< audit_events
```

## 3. Main tables

### `workspaces`
- `id UUID PK`
- `name TEXT NOT NULL`
- `default_currency CHAR(3)`
- `timezone TEXT`
- `created_at`, `updated_at TIMESTAMPTZ`

### `workspace_members`
- `id UUID PK`
- `workspace_id UUID FK`
- `user_subject TEXT`
- `email TEXT`
- `role TEXT CHECK IN ('owner','admin','analyst','viewer','accountant')`
- `status TEXT`
- `created_at TIMESTAMPTZ`
- Unique `(workspace_id, user_subject)`

### `businesses`
- `id UUID PK`
- `workspace_id UUID FK`
- `legal_name TEXT NULL`
- `display_name TEXT NOT NULL`
- `country_code CHAR(2)`
- `created_at`, `updated_at`

### `stores`
- `id UUID PK`
- `workspace_id UUID FK`
- `business_id UUID FK`
- `marketplace_code TEXT`
- `display_name TEXT`
- `external_store_ref TEXT NULL`
- `status TEXT`
- `created_at`, `updated_at`

### `marketplace_connections`
- `id UUID PK`
- `workspace_id UUID FK`
- `store_id UUID FK`
- `connection_method TEXT CHECK IN ('file_upload','oauth_api','extension','other')`
- `status TEXT`
- `credential_ref TEXT NULL` (reference to secret manager; never store plaintext secrets)
- `scopes JSONB`
- `last_sync_at TIMESTAMPTZ NULL`
- `created_at`, `updated_at`

### `imports`
- `id UUID PK`
- `workspace_id UUID FK`
- `store_id UUID FK`
- `uploaded_by TEXT`
- `file_name TEXT`
- `object_key TEXT`
- `sha256 CHAR(64)`
- `file_size_bytes BIGINT`
- `mime_type TEXT`
- `report_type TEXT NULL`
- `schema_version TEXT NULL`
- `period_start DATE NULL`, `period_end DATE NULL`
- `status TEXT`
- `row_count BIGINT NULL`, `accepted_count BIGINT`, `rejected_count BIGINT`
- `error_summary JSONB NULL`
- `created_at`, `updated_at`
- Unique idempotency constraint should be scoped to workspace/store/checksum/import intent, not blindly global.

### `source_records`
- `id UUID PK`
- `workspace_id UUID FK`
- `import_id UUID FK`
- `source_sheet TEXT NULL`
- `source_row_number BIGINT`
- `source_record_key TEXT NULL`
- `record_type TEXT`
- `raw_payload JSONB`
- `normalized_payload JSONB`
- `validation_status TEXT`
- `created_at TIMESTAMPTZ`

### `orders`
- `id UUID PK`
- `workspace_id UUID FK`
- `store_id UUID FK`
- `import_id UUID FK`
- `source_record_id UUID FK`
- `external_order_id TEXT`
- `external_order_item_id TEXT NULL`
- `sku TEXT NULL`
- `order_date TIMESTAMPTZ NULL`
- `currency CHAR(3)`
- `gross_amount NUMERIC(20,6)`
- `discount_amount NUMERIC(20,6) DEFAULT 0`
- `tax_amount NUMERIC(20,6) NULL`
- `net_order_amount NUMERIC(20,6) NULL`
- `status TEXT`
- `created_at TIMESTAMPTZ`

### `settlement_transactions`
- `id UUID PK`
- `workspace_id UUID FK`
- `store_id UUID FK`
- `import_id UUID FK`
- `source_record_id UUID FK`
- `external_transaction_id TEXT NULL`
- `external_order_id TEXT NULL`
- `transaction_type TEXT`
- `transaction_date TIMESTAMPTZ NULL`
- `currency CHAR(3)`
- `amount NUMERIC(20,6)`
- `sign_convention TEXT`
- `created_at TIMESTAMPTZ`

### `reconciliation_runs`
- `id UUID PK`
- `workspace_id UUID FK`
- `store_id UUID FK`
- `period_start DATE`, `period_end DATE`
- `ruleset_version TEXT`
- `status TEXT`
- `started_at`, `completed_at TIMESTAMPTZ NULL`
- `summary JSONB`
- `created_by TEXT`

### `reconciliation_matches`
- `id UUID PK`
- `workspace_id UUID FK`
- `run_id UUID FK`
- `match_group_key TEXT`
- `match_status TEXT CHECK IN ('matched','partial','unmatched','ambiguous','needs_review')`
- `expected_amount NUMERIC(20,6) NULL`
- `actual_amount NUMERIC(20,6) NULL`
- `difference_amount NUMERIC(20,6) NULL`
- `currency CHAR(3)`
- `matching_rule TEXT`
- `rule_version TEXT`
- `evidence JSONB`
- `created_at TIMESTAMPTZ`

Use a join table such as `match_source_records(match_id, source_record_id, role)` to associate many source records with one match.

### `discrepancies`
- `id UUID PK`
- `workspace_id UUID FK`
- `run_id UUID FK`
- `match_id UUID FK NULL`
- `category TEXT`
- `severity TEXT`
- `status TEXT CHECK IN ('open','reviewing','resolved','dismissed','follow_up')`
- `title TEXT`
- `explanation TEXT NULL`
- `difference_amount NUMERIC(20,6) NULL`
- `currency CHAR(3) NULL`
- `assigned_to TEXT NULL`
- `created_at`, `updated_at`

### `discrepancy_notes`
- `id UUID PK`
- `workspace_id UUID FK`
- `discrepancy_id UUID FK`
- `author_subject TEXT`
- `body TEXT`
- `created_at TIMESTAMPTZ`

### `products`
- `id UUID PK`
- `workspace_id UUID FK`
- `store_id UUID FK NULL`
- `sku TEXT`
- `title TEXT NULL`
- `currency CHAR(3)`
- `created_at`, `updated_at`

### `product_costs`
- `id UUID PK`
- `workspace_id UUID FK`
- `product_id UUID FK`
- `cost_type TEXT` (COGS, packaging, shipping, etc.)
- `amount NUMERIC(20,6)`
- `currency CHAR(3)`
- `effective_from DATE`
- `effective_to DATE NULL`
- `source TEXT` (manual/imported)
- `created_by TEXT`

### `exports`
- `id UUID PK`
- `workspace_id UUID FK`
- `created_by TEXT`
- `export_type TEXT`
- `filters JSONB`
- `calculation_version TEXT NULL`
- `object_key TEXT NULL`
- `status TEXT`
- `expires_at TIMESTAMPTZ NULL`
- `created_at TIMESTAMPTZ`

### `audit_events`
- `id UUID PK`
- `workspace_id UUID FK NULL`
- `actor_subject TEXT NULL`
- `action TEXT`
- `resource_type TEXT`
- `resource_id UUID NULL`
- `request_id TEXT NULL`
- `ip_hash TEXT NULL` (only if justified and disclosed)
- `metadata JSONB`
- `created_at TIMESTAMPTZ`

## 4. Indexes and constraints

Recommended initial indexes:
- `workspace_members(user_subject, workspace_id)`
- `stores(workspace_id, marketplace_code)`
- `imports(workspace_id, store_id, created_at DESC)`
- `imports(workspace_id, sha256)`
- `source_records(workspace_id, import_id, source_row_number)`
- `orders(workspace_id, store_id, external_order_id)`
- `settlement_transactions(workspace_id, store_id, external_transaction_id)`
- `reconciliation_matches(workspace_id, run_id, match_status)`
- `discrepancies(workspace_id, status, created_at DESC)`
- `products(workspace_id, store_id, sku)`

Use partial unique indexes only after the actual marketplace identifier semantics are known. Marketplace order IDs may not be globally unique across stores or regions.

## 5. Tenant isolation

- Every query must be scoped by a verified workspace membership.
- Consider PostgreSQL Row-Level Security as defence in depth.
- Set tenant context per transaction when using RLS; never reuse a connection with stale tenant context.
- Background jobs must carry workspace ID and re-check resource ownership.
- Object keys must be namespaced by opaque tenant/workspace IDs, but path obscurity is not authorization.

## 6. Migrations and deletion

- Use Alembic for schema migrations.
- Migrations must be backward-compatible where possible.
- Back up before destructive migrations.
- Define retention periods for original uploads, exports and audit data before public launch.
- Honour deletion requests through a documented workflow, including object storage and derived data, subject to lawful retention obligations.
