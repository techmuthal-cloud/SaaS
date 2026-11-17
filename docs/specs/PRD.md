# Product Requirements Document (PRD)

- Product: SellerFlow AI
- Status: Draft for discovery and MVP planning
- Audience: Founder, product, design, engineering, QA and AI coding agents

## 1. Product vision

SellerFlow AI is a financial operations workspace for e-commerce sellers. It converts fragmented marketplace reports into normalized financial records, reconciles expected and actual settlements, highlights unexplained differences, and calculates profitability from explicit cost inputs.

### Product promise

**Know what you should have received, what you actually received, and what you truly earned.**

### Problem statement

Sellers may need to work across order exports, settlement statements, fee reports, refund/return reports, advertising exports, bank statements and product cost sheets. These sources can use different identifiers, date ranges, columns and aggregation levels. Manual spreadsheet work makes it difficult to trace discrepancies and calculate profitability consistently.

The product hypothesis is that sellers will pay for a trustworthy workflow that saves reconciliation time and improves financial visibility. This hypothesis must be validated through interviews, observed workflows and paid pilots.

## 2. Target users and jobs to be done

### Primary: owner-operated marketplace seller
- Runs one or more marketplace stores.
- Uses spreadsheets or a basic accounting workflow.
- Wants to identify settlement differences and understand product margins.
- Has limited time and does not want enterprise implementation complexity.

### Secondary: accountant or e-commerce agency
- Supports multiple seller businesses.
- Needs client separation, repeatable monthly processing and exportable evidence.
- Needs a review workflow and audit history.

### Tertiary: growing D2C brand
- Sells through a marketplace plus its own storefront.
- Needs consolidated channel visibility and product profitability.

### Jobs to be done
1. When I receive a marketplace settlement, help me compare it with the underlying orders and charges.
2. When a difference appears, show the source records and possible explanations so I can investigate it.
3. When I review a product, show profit only from the costs and revenue inputs that are available and disclosed.
4. When month-end arrives, help me generate a repeatable report for myself or my accountant.

## 3. Goals and non-goals

### MVP goals
- Make report upload and validation understandable.
- Normalize one selected marketplace's report set into a canonical model.
- Match supported financial records deterministically.
- Flag unmatched or inconsistent records with source traceability.
- Provide a basic profitability view using explicit seller-entered/imported costs.
- Export a useful reconciliation workbook.
- Maintain tenant isolation, import history and audit events.

### Non-goals for MVP
- Full ERP, inventory, order management or warehouse management.
- Automated tax filing or statutory GST compliance.
- Guaranteed recovery of marketplace funds.
- Automatically raising disputes or claims without user review.
- Supporting every marketplace or report type at launch.
- LLM-generated financial calculations.
- Native mobile apps before web workflow validation.

## 4. Product principles

1. **Evidence before explanation:** every financial output must link to imported source records or explicitly entered inputs.
2. **Deterministic arithmetic:** financial totals and matches are calculated by versioned rules, not an LLM.
3. **Visible uncertainty:** unresolved, ambiguous and partial matches must be labelled clearly.
4. **User control:** users can review, correct mappings, reject suggestions and delete eligible data.
5. **Progressive complexity:** simple seller workflow first; accountant and advanced controls later.
6. **No false promises:** don't claim guaranteed recovery, tax compliance or universal marketplace support.

## 5. MVP scope

### P0 – required
- Email-based signup/login through a managed identity provider.
- Business, store and user profile creation.
- Workspace membership and owner role.
- Upload CSV/XLSX files with size/type validation.
- Import status and import history.
- File classification using deterministic signatures plus optional AI suggestion.
- User-confirmed column mapping.
- Canonical order, settlement, fee, refund and payout records for selected adapter.
- Deterministic matching and discrepancy categories.
- Source-record viewer.
- Basic SKU cost input and profit calculation.
- Export CSV/XLSX reconciliation results.
- Audit log for material user actions.
- Tenant-scoped access control and data deletion request path.

### P1 – after MVP validation
- Second and third marketplace adapters.
- Scheduled/automated imports where approved official access exists.
- Multiple stores per workspace.
- Accountant/client workspace.
- Custom report builder.
- Advertising cost import.
- AI assistant grounded in reconciled data.
- Subscription billing and metered usage.

### P2 – advanced
- Bank statement reconciliation.
- Dispute package generation and workflow tracking.
- Accounting software integrations.
- Forecasting and anomaly monitoring.
- Advanced agency portfolio reporting.

## 6. Core user stories and acceptance criteria

### US-01: Upload a report
As a seller, I want to upload a report so that I can process it without manually rebuilding the spreadsheet.

Acceptance:
- Accept only configured MIME types and extensions.
- Enforce configurable file and row limits.
- Store file metadata and checksum.
- Show uploaded, validating, needs-mapping, processing, completed or failed status.
- Never expose another tenant's file or import.

### US-02: Map columns
As a seller, I want to map report columns to known fields and save the mapping.

Acceptance:
- Show detected columns and sample values.
- Mark required and optional fields.
- Reject invalid type conversions with row-level errors.
- Save mapping version and user who approved it.

### US-03: Reconcile transactions
As a seller, I want to compare expected and actual settlement values.

Acceptance:
- Matching rules are versioned and deterministic.
- Exact matches, partial matches, unmatched records and ambiguous matches are distinct states.
- Every result links to source record IDs.
- Totals reconcile to the selected source report within configured rounding tolerance.

### US-04: Investigate discrepancy
As a seller, I want to understand a mismatch.

Acceptance:
- Display expected amount, actual amount, difference, currency and relevant dates.
- Display source rows and matching rule used.
- Provide possible reasons only when supported by data; label them as hypotheses otherwise.
- Allow review status and notes.

### US-05: Understand product profitability
As a seller, I want to calculate a product's contribution using known revenue and costs.

Acceptance:
- Show each included and missing cost component.
- Do not treat unknown values as zero without an explicit user setting.
- Clearly label estimates and incomplete cost coverage.
- Allow export of calculation detail.

### US-06: Export results
As a seller, I want to download the results for review and accounting preparation.

Acceptance:
- Export is tenant-scoped and time-limited where a download URL is used.
- Export includes generation time, selected period, currency, calculation version and caveats.
- Export values match the UI and underlying query results.

## 7. Success metrics

Instrument baseline metrics before setting hard growth targets.

### Activation
- Percentage of new workspaces that complete a first successful import.
- Time from signup to first completed reconciliation.
- Percentage of uploads requiring manual mapping intervention.

### Product value
- Percentage of imports with usable reconciliation output.
- Number and proportion of matched, unmatched and ambiguous records.
- Percentage of discrepancies opened and resolved/annotated.
- Repeat processing rate in the next reporting cycle.

### Reliability
- Import failure rate by adapter and file type.
- Duplicate import prevention rate.
- Financial total variance against independently verified fixtures.
- Background job retry and dead-letter rates.

### Commercial
- Demo-to-activated-workspace conversion.
- Activated-to-paid conversion after pricing is tested.
- Paid retention, churn and support burden.

Avoid treating downloads, page views or AI chat messages as primary product success metrics.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Marketplace format changes | Versioned adapters, fixtures, schema drift alerts and manual upload fallback |
| Incorrect financial matches | Conservative matching, ambiguity state, traceability and human review |
| Incomplete cost data | Explicit coverage labels and missing-input warnings |
| Sensitive business data exposure | Tenant isolation, encryption, least privilege, retention controls and audits |
| Low willingness to pay | Interviews, concierge pilots and paid validation before broad development |
| Overbuilt MVP | P0 scope lock and release gates |
| AI hallucinations | Grounded explanations only; deterministic rules for arithmetic |

## 9. Product decisions still requiring validation

- Which marketplace and report family should be first.
- Whether initial customer acquisition should focus on sellers or accountants.
- Exact file size, row and monthly processing limits.
- Pricing and free-trial design.
- Which cost fields sellers can reliably provide.
- Whether the first adapter can use official API access or must begin with manual exports.
