# Integration Strategy

## 1. Integration principles

- Start with user-uploaded reports to validate the core workflow.
- Add automated marketplace APIs only after confirming official access, permissions, commercial/partner restrictions and current technical documentation.
- Never scrape or automate a seller portal in violation of platform terms.
- Keep marketplace-specific logic in adapters.
- Clearly distinguish supported, limited, beta, planned and unsupported connectors.

## 2. Integration roadmap

### MVP
- CSV and XLSX upload.
- One marketplace adapter chosen through discovery.
- Manual mapping for unfamiliar report layouts.
- Export results to CSV/XLSX.

### Next phase
- Add second marketplace based on customer demand and sample-report validation.
- Add scheduled imports only where official APIs or approved mechanisms support them.
- Add advertising and bank statement import as separate adapters.

### Later
- Accounting software integration.
- Webhooks/event updates where providers support them.
- Agency-level multi-store automation.

## 3. Connector support status

Each connector must display:
- `Available`: tested and supported for stated report types.
- `Limited`: only specified workflows/files are supported.
- `Beta`: opt-in, known limitations disclosed.
- `Planned`: not currently available.
- `Unsupported`: explicitly unavailable.

## 4. Adapter contract

Each adapter must define:
- Marketplace identifier and region.
- Report types.
- Accepted file types and schema versions.
- Required and optional columns.
- Identifier matching rules.
- Sign convention for fees, credits, refunds and payouts.
- Currency and timezone interpretation.
- Pagination/rate limits for APIs.
- Authentication scopes and token handling.
- Known unsupported scenarios.
- Fixture data and expected outputs.

## 5. Integration readiness checklist

A connector cannot be labelled production-ready until:
- Official documentation and access terms are reviewed.
- Authentication and scopes are approved.
- At least representative normal, edge and failure files are tested.
- Currency/date/sign conventions are documented.
- Reconciliation totals are independently verified.
- Rate limits, retries and token refresh are tested (API connectors).
- Data deletion and credential revocation are supported.
- User-facing limitations are documented.

## 6. Failure handling

- Expired/revoked credentials: prompt reconnect; do not endlessly retry.
- Rate limited: respect provider retry headers and backoff.
- Schema drift: pause processing and request mapping review; do not guess silently.
- Partial data: mark result partial and list missing source types.
- Duplicate webhook: enforce idempotency.
- Provider outage: preserve job state and retry only when safe.

## 7. Integration security

- Store credentials in a secret manager or encrypted credential store.
- Never return access/refresh tokens to the browser after initial secure exchange.
- Request minimum scopes.
- Encrypt tokens at rest and rotate/revoke when required.
- Avoid logging request headers or payloads containing credentials.
