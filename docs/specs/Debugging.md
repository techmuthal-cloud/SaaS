# Debugging and Troubleshooting

## 1. Diagnostic principles

- Start with request ID, import ID, workspace ID and job ID.
- Inspect status metadata before inspecting raw files.
- Do not log full financial rows, access tokens or marketplace credentials.
- Reproduce with a synthetic or authorized anonymized fixture.
- Preserve original file and processing version when investigating a report defect.
- Never “fix” a financial mismatch by manually changing stored totals without a correction event and audit trail.

## 2. Import failure playbook

### Upload fails
Check:
- Authenticated user and workspace role.
- Upload URL expiry and scope.
- Bucket policy and CORS.
- File size and allowed content type.
- Object storage availability.

### File uploaded but no processing
Check:
- Import state in PostgreSQL.
- Queue connection and queue name.
- Worker health and task registration.
- Dead-letter/retry metadata.
- Whether the transaction creating the job was committed.

### Parser rejects a valid-looking file
Check:
- Actual file signature and encoding.
- Header row and merged cells.
- Sheet names and hidden rows.
- Date/decimal separators.
- Report schema version.
- Mapping version and required field definitions.

Do not bypass parser validation globally. Add a versioned adapter change and fixture.

## 3. Reconciliation mismatch playbook

1. Identify reconciliation run and ruleset version.
2. Open the match/discrepancy record.
3. Inspect referenced source records and original row locations.
4. Verify currency, date/timezone and sign convention.
5. Confirm records are from the same store and reporting period.
6. Check duplicate import prevention and source ID uniqueness assumptions.
7. Re-run independently with the golden fixture.
8. If logic is wrong, create a regression test before changing the rule.
9. Recalculate into a new run/version; preserve previous output and audit history.

## 4. Profit calculation issue

Check:
- Which revenue fields are included.
- Whether tax is included/excluded consistently.
- Cost profile effective dates.
- Refund/return allocation.
- Currency mismatch or conversion source.
- Missing cost values incorrectly treated as zero.
- Advertising and shipping costs double-counted.
- Calculation version.

## 5. Authentication/authorization issues

Check token issuer, audience, expiry, signature and JWKS refresh. Then verify workspace membership and role from the database. Do not accept a role or workspace claim supplied only by the client.

## 6. Useful observability fields

- `request_id`
- `workspace_id` (opaque ID)
- `user_subject` (pseudonymous/provider subject as appropriate)
- `import_id`
- `job_id`
- `adapter_code`
- `adapter_version`
- `ruleset_version`
- `duration_ms`
- `rows_total`, `rows_valid`, `rows_rejected`
- `error_code`

Avoid logging full rows, personal identifiers or secrets. Use structured error codes and redacted context.

## 7. Incident escalation

Escalate immediately for suspected cross-tenant access, exposed credentials, altered financial results, unauthorized marketplace actions, data loss or malware processing. Follow Security.md incident response.
