# Security and Privacy Requirements

## 1. Security objectives

Protect customer financial reports, identity data, marketplace credentials, reconciliation results and exports from unauthorized access, accidental disclosure, tampering and loss.

## 2. Threat model

| Threat | Example | Required controls |
|---|---|---|
| Cross-tenant access | User guesses another workspace ID | Server-side membership checks, RLS defence in depth, tenant tests |
| Malicious file | Crafted XLSX/ZIP or formula payload | File signature checks, parser limits, archive limits, isolated workers, safe export escaping |
| Credential exposure | API token committed to Git | Secret manager, scanning, key rotation, least privilege |
| Injection | CSV cell rendered as HTML | Output encoding, sanitization and safe rendering |
| Duplicate processing | Retry creates duplicate financial records | Idempotency keys, unique constraints and transaction-safe jobs |
| AI prompt injection | Spreadsheet cell contains instructions | Treat file contents as untrusted data; isolate prompts and tools |
| Data exfiltration | Raw report sent to external LLM | Data minimization, user disclosure/consent, provider review and optional opt-out |
| Insecure download | Public object URL | Private bucket, short-lived scoped URL and authorization check |
| Insider misuse | Staff accesses customer report | Least privilege, audited support access and limited retention |

## 3. Data classification

- Public: marketing pages and public documentation.
- Internal: product telemetry without customer financial content.
- Confidential: business profiles, store metadata, transaction and profitability records.
- Restricted: identity tokens, marketplace credentials, uploaded raw reports, bank data and support attachments containing financial records.

## 4. Required controls

### Application
- Enforce authorization on every object access.
- Validate input types, lengths, ranges and enumerations.
- Use parameterized database queries/ORM.
- Apply CSRF controls where cookie-based sessions are used.
- Apply rate limits and request size limits.
- Use secure headers and a restrictive Content Security Policy.
- Avoid exposing detailed exceptions to clients.

### Files
- Private object storage only.
- Validate actual file signatures, not only extension/MIME header.
- Limit file size, rows, sheets, archive expansion and processing time.
- Disable macros; do not execute formulas or embedded content.
- Render cell values as text.
- Prevent spreadsheet formula injection in CSV/XLSX exports by escaping cells beginning with dangerous formula characters where applicable.
- Scan files with a malware service if risk and deployment model require it.

### Database
- TLS to managed services.
- Encrypted backups and storage.
- Least-privileged service accounts.
- RLS or equivalent tenant isolation defence.
- Regular backup restore tests.
- Audit privileged operations.

### AI
- Send the minimum necessary data.
- Do not send secrets, full bank details or unrelated customer records.
- Treat imported cell text as untrusted input, never as system instruction.
- Require retrieval scope to be tenant- and permission-filtered before prompt construction.
- Do not give an AI agent direct write access to financial ledgers.
- Keep prompts, model versions and output metadata for review where appropriate, without retaining unnecessary sensitive text.

## 5. Privacy and retention

Before launch, publish a clear privacy notice covering:
- Data collected and purposes.
- Marketplace connection scopes.
- Processors/subprocessors.
- Storage locations and cross-border transfers where applicable.
- Retention periods for raw files, normalized records, exports and audit data.
- Deletion and access request process.
- AI provider usage and opt-out/consent controls.

Do not invent compliance certifications. Obtain legal review for applicable Indian data protection, consumer, tax and payment requirements before production launch.

## 6. Incident response

1. Detect and classify incident.
2. Contain affected credentials, jobs, access paths or storage.
3. Preserve relevant security logs.
4. Determine tenants/data affected.
5. Notify internal owner and obtain legal/privacy advice on required external notifications.
6. Remediate and rotate secrets.
7. Verify recovery and monitor recurrence.
8. Document root cause and corrective actions.

## 7. Release security checklist

- Tenant isolation tests pass.
- No secrets in Git or build artifacts.
- Dependencies scanned.
- File parser resource limits tested.
- Export formula injection checked.
- Authentication and authorization tests pass.
- Backups and restore procedure tested.
- Retention and deletion workflow documented.
- Admin/support access audited.
- Privacy and terms pages reviewed.
