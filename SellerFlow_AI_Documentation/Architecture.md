# System Architecture

## 1. Architecture overview

Use a modular monolith for the MVP: one FastAPI codebase with clear domain modules, one worker process, one PostgreSQL database, Redis for jobs and private object storage. Split services only when operational scale or team boundaries justify it.

```text
Browser
  |
  v
Next.js Web App ---- Managed Identity Provider
  |
  | HTTPS + access token
  v
FastAPI API
  |---- PostgreSQL (tenants, users, imports, normalized records, matches)
  |---- Private Object Storage (original reports and exports)
  |---- Redis Queue
             |
             v
        Worker Processes
          |-- File validation and parsing
          |-- Marketplace adapters
          |-- Canonical normalization
          |-- Reconciliation rules
          |-- Profit calculations
          |-- Export generation
          |-- Optional AI enrichment
```

## 2. Logical modules

- `identity`: identity claims, workspace membership and authorization.
- `workspaces`: businesses, stores and team members.
- `integrations`: marketplace adapter registry and connection metadata.
- `imports`: upload, file validation, parser dispatch and import lifecycle.
- `normalization`: canonical records and provenance.
- `reconciliation`: deterministic matching rules and result storage.
- `discrepancies`: exception classification, review status and notes.
- `profitability`: cost inputs and margin calculations.
- `reports`: export definitions and generated artifacts.
- `ai_assistant`: grounded retrieval and explanation only.
- `billing`: subscriptions and usage, added when commercial launch requires it.
- `audit`: append-only record of security-relevant and financial workflow actions.

## 3. Deployment units

### Web
Next.js application. It must not contain marketplace secrets, database service-role keys or financial matching logic that users can bypass.

### API
FastAPI handles authentication verification, authorization, validation, domain commands, metadata queries and job creation. It should return job IDs for long-running processing.

### Worker
Workers parse and process files. Use bounded concurrency, resource limits, retries only for transient errors and a dead-letter state after retry exhaustion.

### Scheduler
A separate scheduled process may later initiate approved periodic imports and report jobs. MVP can omit it.

### Data services
PostgreSQL is the system of record. Redis is transient queue/cache infrastructure. Object storage holds immutable originals and generated exports. Do not use object storage paths as authorization boundaries; authorize every access through the API.

## 4. Import and reconciliation data flow

1. API verifies user and workspace role.
2. API creates an import record and a short-lived upload target or accepts a streamed upload.
3. File is stored in a private bucket; checksum and metadata are recorded.
4. API enqueues a processing job using the import ID.
5. Worker retrieves file using service credentials scoped to the job.
6. File validator checks type, content signature, size, archive safety and parser limits.
7. Adapter detects report type and schema version.
8. Mapping service resolves known columns or requests user confirmation.
9. Normalizer writes staging/canonical records with provenance.
10. Validator records row-level errors and warnings.
11. Reconciliation engine runs a versioned ruleset.
12. Results, discrepancies and source links are committed in transactions.
13. API exposes status and results to the tenant-authorized user.
14. Export worker creates a private artifact and an expiring download link after authorization.

## 5. Adapter architecture

Each marketplace adapter implements a stable interface:

```python
class MarketplaceAdapter(Protocol):
    marketplace_code: str
    def identify(self, file_metadata, sample_rows) -> DetectionResult: ...
    def validate(self, file_ref, report_type) -> ValidationResult: ...
    def parse(self, file_ref, mapping) -> ParsedBatch: ...
    def normalize(self, parsed_batch) -> CanonicalBatch: ...
```

Adapters must provide:
- Supported report types and schema versions.
- Required/optional fields.
- Identifier semantics and sign conventions.
- Timezone and currency handling.
- Fixtures with known-good expected outputs.
- Known limitations and unsupported cases.

## 6. Reconciliation engine

Separate the matcher from the marketplace parser. Use canonical records and a configured strategy sequence such as:
1. Exact stable source transaction/order ID match.
2. Exact composite key match when documented identifiers are unavailable.
3. Constrained amount/date/currency matching only when safe.
4. Ambiguous candidate group when multiple plausible matches exist.
5. Unmatched state when no eligible match is found.

Do not automatically select a fuzzy candidate when evidence is insufficient. Matching rules must have a version, inputs, tolerance and audit metadata.

## 7. AI boundary

AI may:
- Suggest file/report type from headers and non-sensitive samples.
- Suggest column mappings for user confirmation.
- Explain already-computed differences using retrieved source facts.
- Summarize trends with explicit data coverage caveats.

AI may not:
- Calculate or alter ledger totals.
- Create transactions or matches without deterministic validation.
- Infer a missing cost as zero.
- claim tax compliance or recovery certainty.
- access another tenant's data.
- send raw full reports to a model unless data minimization, consent, provider terms and retention have been reviewed.

## 8. Scaling and resilience

- Use pagination and appropriate indexes for transaction lists.
- Process large files asynchronously with chunked parsing.
- Use import-level locks or idempotency constraints to prevent duplicate processing.
- Keep worker jobs retry-safe.
- Store job state in PostgreSQL; queue state alone is insufficient.
- Add per-tenant quotas and backpressure.
- Add dead-letter queue and admin replay workflow.
- Test backup restoration, not only backup creation.

## 9. Architecture decisions to record (ADRs)

Create ADRs for: identity provider, first marketplace adapter, API hosting, worker/queue, file storage, AI provider, payment provider, tenant strategy, report retention and observability stack.
