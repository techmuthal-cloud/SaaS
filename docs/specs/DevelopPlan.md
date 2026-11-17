SELLERFLOW AI  |  PRODUCT & ENGINEERING BLUEPRINT

SELLERFLOW AI

Product Development Blueprint

Product strategy • Financial domain • Architecture • Security • Delivery roadmap

Version 1.0  |  17 November 2026

Prepared as the implementation baseline for the SellerFlow AI repository


Confidential working document  •  17 November 2026  •  

SELLERFLOW AI  |  PRODUCT & ENGINEERING BLUEPRINT

Document control

Field

Details

Document

SellerFlow AI — Product Development Blueprint

Version / date

1.0 / 17 November 2026

Purpose

Translate the repository review and market findings into a buildable, testable development plan.

Product scope

Financial intelligence and reconciliation for Indian marketplace sellers, CAs and e-commerce agencies.

Repository reviewed

techmuthal-cloud/SaaS — commit ca389d54953192d32206c4ca1f4558f6b1acd13e

Status

Proposed target-state plan; not a statement that the recommended features are already implemented.

How to read this document

This blueprint combines the findings in the supplied Senior Product & Engineering Review (dated 17 November 2026) with the development recommendations established in this conversation. Repository findings below are attributed to that review; they have not been independently re-run as part of producing this document. Market figures, competitor pricing and marketplace policy statements are time-sensitive and should be revalidated before they are used in public marketing, pricing or tax logic.

Status language: Current / Reported means the supplied review describes the repository that way; Recommended means a proposed change; Acceptance criterion means an objective test required before a feature is called complete.

1. Executive direction

SellerFlow AI should evolve from a generic marketplace CSV cleaner into accountant-grade financial intelligence for Indian marketplace sellers and the professionals who manage their books.

Positioning: “Know what you earned. Verify what reached your bank. Track every deduction. Find every unexplained difference.”

The product's competitive advantage should not be a larger dashboard or a generic AI chatbot. It should be a trustworthy financial evidence trail: every normalized amount tied to its source row, every calculation reproducible from a versioned rule, every settlement matched to real bank evidence, and every unresolved difference clearly labelled as an investigation.

Primary customer segments

Segment

Primary job to be done

Product priority

Marketplace seller

Understand settlement deductions, bank credits, returns and actual profitability.

Core self-serve workflow

Chartered accountant / accounting firm

Close multiple seller books accurately, reconcile TDS/TCS and post entries into Tally.

High-value paid segment

E-commerce agency

Monitor many seller accounts, detect exceptions and prepare monthly reporting.

Multi-client workflow after core accuracy

Product principles

Financial calculations are deterministic; AI may explain or assist, but never calculate or alter ledger values.

Evidence before claims: no “found money” or overcharge statement without a reproducible rule and source evidence.

Never invent a date, amount, fee, reserve, refund or bank credit. Missing data must remain explicitly missing.

Separate order economics, marketplace settlement accounting and cash movement.

One marketplace working correctly is more valuable than three advertised adapters that silently return zero.

Security and tenant isolation are release blockers, not later enhancements.

2. Current-state assessment

The supplied review describes the repository as a clickable prototype with a useful product specification, rather than a production-ready MVP. It reports that the code and documentation are out of alignment. Treat these as audit findings from the supplied review, not as fresh independent test results.

Area

Finding reported in review

Business / technical impact

Amazon reconciliation

4 of 4 fixture orders were classified as fee overcharges; ₹2,916.20 was labelled as recoverable despite normal fees.

Destroys trust; may lead sellers to file invalid disputes.

Flipkart and Meesho adapters

Fixture headers with underscores did not match space-based mappings; rows parsed with ₹0 values.

Two advertised marketplace integrations are not reliable.

Settlement cycle

Hardcoded settlement ID/dates, synthetic reserve percentages and bank deposit defaulting to calculated payout.

Dashboard can show a balanced result without real bank evidence.

Security

No route authentication or tenant isolation; upload path uses unsanitized filename.

Critical exposure of customer financial data and file-system risk.

Dates and returns

Some dates parsed but not persisted; fallback dates and hardcoded policy windows used.

Return leakage and cohort analysis can be wrong.

AI capability

Review found no LLM, embeddings or ML implementation.

Brand promise exceeds shipped capability.

Testing

Two tests reported, neither exercising marketplace adapters or upload-to-reconciliation flow.

Critical regressions can pass CI unnoticed.

Frontend/backend structure

Large client-side page, hardcoded localhost API URL, large router and synchronous import processing.

Hard to maintain, scale, test and deploy.

Immediate product decision

Freeze new marketplace and AI feature claims until the financial engine and security baseline pass their acceptance tests. Do not delete the prototype; use it as a UI and workflow reference while replacing incorrect financial logic.

3. Market and positioning strategy

3.1 Market interpretation

The supplied research cites strong growth in Indian e-commerce and large seller bases across Amazon, Flipkart and Meesho. It also estimates 350,000–500,000 potentially serviceable higher-volume seller accounts by applying an assumed 10–15% filter to a broad seller-account estimate. This is a planning hypothesis, not a validated serviceable obtainable market (SOM), and should not be presented as a measured customer count.

The practical opportunity is narrower and more actionable: sellers and CAs who repeatedly need to explain why marketplace settlement values differ from bank credits, understand deductions, reconcile TDS/TCS, account for returns and prepare month-end books.

3.2 Marketplace fee implications

The supplied review notes zero-referral/zero-commission changes for certain lower-priced products on Amazon India and Flipkart, and a zero-commission model at Meesho. Because fee policies, categories, fulfilment types and effective dates change, treat these statements as dated market context and verify the official marketplace schedule before implementing any rule.

Do not build the product around commission overcharge detection alone.

Prioritize shipping and weight-handling charges, closing fees, returns/RTO, reverse logistics, adjustments, penalties, reserves, ads and reimbursement claims.

Use effective-dated rate cards with marketplace, category, price band, weight slab, fulfilment channel and applicable date range.

Keep TDS and GST TCS as separate ledger concepts. Tax rates and legal sections must be reviewed against current official guidance and professional advice before release.

3.3 Competitive positioning

Competitive group

Observed positioning in supplied research

SellerFlow response

TheEcomWay

Low-cost self-serve marketplace reconciliation.

Compete on accountant-grade evidence, tax reconciliation and CA workflows—not only price.

Unicommerce / EasyEcom

Reconciliation bundled with OMS/WMS ecosystems.

Offer a lighter finance-focused product for sellers who do not want a full OMS.

Vin Reco / Vinculum

Marketplace reimbursement and reconciliation capabilities.

Differentiate with India-specific bank, Tally and TDS/TCS workflows.

Cointab and generic finance tools

Broad enterprise finance reconciliation; higher price positioning.

Focus on marketplace-specific semantics and SMB/CA usability.

MaruTally

Tally-centric marketplace accounting.

Build configurable, auditable Tally posting and broader settlement-to-bank evidence.

A2X / Link My Books / Sellerboard

Mature global accounting or profit tooling.

Emphasize Indian marketplaces, Indian tax deductions and local accounting workflows.

Competitor feature and pricing statements in the supplied research are vendor/site claims or secondary-source summaries. Recheck current plan pages and product demos before making a comparison chart or pricing decision.

3.4 Positioning statement

For Indian marketplace sellers, CAs and e-commerce agencies who need reliable month-end books, SellerFlow AI is an evidence-first financial intelligence platform that reconciles marketplace settlements to bank deposits, explains deductions, separates tax withholdings and prepares accounting exports. Unlike generic report cleaners, every result is traceable to source data and versioned rules.

3.5 Validation before scaling

Interview at least 15 sellers across Amazon, Flipkart and Meesho, including low- and high-volume accounts.

Interview at least 5 CAs or accounting firms who currently close marketplace books.

Collect anonymized real settlement, order, returns and bank statement samples with written permission.

Measure how long month-end reconciliation currently takes and which exceptions cause the most rework.

Run a paid pilot; willingness to pay is stronger evidence than survey interest.

4. Product scope and functional requirements

4.1 Financial Core v1 — the first release target

The first commercially meaningful release should support one marketplace—Amazon India—end to end. It must import an actual settlement report, normalize transaction lines, explain the settlement calculation, import a bank statement and match the settlement to the real bank credit. Flipkart and Meesho should be added only after their own real-report fixtures pass.

Capability

Functional requirement

Release evidence

Workspace and identity

Users sign in; every request is authorized against workspace membership and role.

Cross-tenant access tests fail closed.

Amazon settlement import

Parse settlement header, settlement ID, period, deposit date, total amount and all transaction lines.

Golden-file fixtures match expected normalized rows.

Canonical financial ledger

Preserve sales, fees, refunds, reserves, adjustments, TDS and TCS as distinct transaction categories.

Every ledger line has source-file and source-row provenance.

Fee audit

Calculate expected fees from a versioned rate card and compare only like-for-like fee categories.

Formula, inputs, tolerance and rule version are inspectable.

Bank import

Import supported bank CSV formats and normalize value date, narration, debit, credit and balance where present.

Real bank credit is not inferred from settlement payout.

Settlement-to-bank matching

Match by settlement reference, amount and configured date window; support partial, delayed and unmatched credits.

Match result includes rule, confidence and evidence.

Discrepancy workflow

Classify as matched, short-paid, over-paid, pending/reserve, missing or needs-data.

No unsupported claim language or synthetic amounts.

TDS/TCS reporting

Keep income-tax TDS and GST TCS separate and summarize by period.

Reconciliation report identifies source and tax period.

Exports

Export CSV/XLSX and Tally XML with configurable ledger mappings.

Export totals tie back to the selected ledger period.

4.2 Core screens

Route / screen

Purpose

Important UI behaviour

/

Marketing landing page with clear target customer and proof-led value proposition.

Server-rendered, SEO-ready; no fake metrics.

/pricing

Transparent plans and usage limits.

Clearly label prices as pilot pricing until validated.

/login

Authentication and account recovery.

Secure provider integration; no mock-only login.

/app/[workspaceId]/overview

Financial health and current reconciliation status.

Show matched, pending and unresolved values separately.

/imports

Upload and import history.

Real progress, job status, errors by row, duplicate detection.

/settlements

Settlement cycle and line-item view.

Timeline from settlement period to deposit and bank credit.

/bank-reconciliation

Bank transactions and settlement matching.

Manual review and match/unmatch audit trail.

/discrepancies

Exception investigation queue.

Evidence, rule, amount, status and owner.

/returns

Returns/RTO and reimbursement tracking.

Require returns evidence and policy dates.

/tax-reconciliation

TDS and GST TCS summaries.

Separate tax types and periods; avoid tax advice claims.

/exports

Accounting exports and history.

Preview, ledger mapping and audit event.

/clients

CA/agency client portfolio.

Only enabled after role and tenant controls are proven.

/settings

Workspace, store, roles, integrations and retention settings.

Sensitive changes audited.

4.3 Discrepancy vocabulary

Status

Meaning

Matched

Expected and actual values match within the configured tolerance.

Short-paid

Evidence indicates actual cash or settlement amount is below the expected amount.

Over-paid

Actual amount exceeds the expected amount; investigate classification before treating as gain.

Pending / reserve

Amount is explicitly held or deferred in marketplace data.

Missing

A required expected or actual record is absent from the imported evidence.

Needs data

Insufficient source data or rate-card coverage to make a reliable determination.

A discrepancy is an investigation record, not itself a financial transaction. It must never be added to or subtracted from the ledger as if it were cash.

5. Financial domain model and calculation rules

5.1 Three separate financial views

View

Question answered

Primary records

Order economics

What was sold, refunded and what did the item cost?

Orders, order items, product costs, refunds, returns.

Marketplace earnings

What did the marketplace post, defer, release or adjust?

Settlement headers, settlement lines, fee lines, reserves, tax deductions.

Cash movement

What actually reached or left the bank?

Bank transactions and settlement-bank matches.

5.2 Required dates

order_date — when the customer order was placed.

transaction_date — date associated with a marketplace financial event.

posted_date — when the marketplace posted the event, if distinct.

release_date — when a deferred/reserved amount was released.

settlement_date — settlement cycle date or period reference.

bank_value_date — date the bank recognizes the credit/debit.

return_date and refund_date — separately persisted when provided.

Store timestamps in UTC where applicable and preserve the marketplace-local business date. Do not replace missing source dates with created_at or arbitrary default windows.

5.3 Fee audit calculation

For each order line and applicable fee category, calculate expected fee using the effective rate-card version for the marketplace, category, price band, weight slab, fulfilment channel and transaction date. Compare that expected fee only with actual lines that represent the same fee category.

Illustrative rule: discrepancy = actual_fee − expected_fee. Apply a documented tolerance for rounding and marketplace-specific precision. If the expected fee cannot be computed because required attributes or an applicable rate card are missing, return “Needs data”; do not assume zero.

Never compare gross order value directly with gross less normal fees and label the difference an overcharge.

Do not classify every negative settlement line as a refund.

Do not infer bank deposit amount from calculated marketplace payout.

Do not create synthetic reserve percentages or default order values.

Use Python Decimal and database NUMERIC; expose money values to the API as decimal strings.

5.4 Reconciliation provenance

Every normalized transaction and reconciliation result should retain workspace/store, import ID, source file ID, source row number, original raw payload or secure reference, normalized type, amount, currency, date fields, parser version, mapping version, rate-card version and reconciliation-run ID.

5.5 Waterfall rules

The financial waterfall must be a presentation of ledger components, not a second calculation that subtracts discrepancies on top of fees. A discrepancy explains a difference between expected and actual; it must not be double-counted as another cash outflow.

6. Target technical architecture

Use a modular monolith. Keep one product and deployment boundary with clear domain modules. Microservices and Kubernetes add operational cost without solving the immediate correctness and security risks.

Layer

Recommended technology / responsibility

Web

Next.js 16 App Router, TypeScript, React 19, Tailwind CSS, accessible component system.

Data fetching / UI

TanStack Query, TanStack Table, React Hook Form + Zod, Recharts where useful.

API

FastAPI with Pydantic request/response schemas and OpenAPI-generated TypeScript types.

Domain modules

Ingestion, adapters, ledger, settlements, reconciliation, bank, tax, returns, claims, exports, billing, AI.

Persistence

PostgreSQL, SQLAlchemy 2.0, Alembic migrations; Decimal/Numeric financial types.

Async processing

Redis-backed worker queue for imports, reconciliation and exports; job state persisted in PostgreSQL.

File storage

Private S3-compatible storage such as S3/R2; presigned upload/download; encryption at rest.

Observability

Structured logs, error tracking, traces, import/job metrics and audit events.

Deployment

Web hosting plus API/worker and managed PostgreSQL/Redis; choose region and vendors after cost, residency and reliability review.

6.1 Import pipeline

Client requests an upload target; API validates identity, workspace permissions and file limits.

File is stored privately under a generated identifier, never a user-controlled path.

API creates an import/job record and returns HTTP 202 with import_id.

Worker detects report type, parses headers and validates schema.

Adapter normalizes records while preserving raw row provenance.

Validation and duplicate checks run; errors are reported per row without silently dropping money values.

Ledger records are written idempotently in a transaction.

Reconciliation runs with explicit parser, mapping and rate-card versions.

UI polls or subscribes to job status and displays a reproducible result.

6.2 Adapter contract

Each marketplace adapter should declare supported report types, header aliases, required fields, date/amount semantics, parser version and golden-file fixtures. Header normalization should handle case, spaces, underscores and hyphens consistently, but mappings must still be explicit and tested.

6.3 API conventions

All protected endpoints require authentication and workspace authorization.

List endpoints support server-side pagination, filtering and sorting.

GET endpoints must not create workspaces or trigger other side effects.

Imports and large exports are asynchronous jobs with stable job IDs.

Use a consistent error response schema and API versioning.

Use idempotency keys for upload and reconciliation operations where retries could duplicate records.

Generate TypeScript API types from FastAPI OpenAPI; do not maintain duplicate hand-written contracts.

7. Data model

Domain

Core tables / entities

Identity & tenancy

users, workspaces, workspace_members, businesses, stores, marketplace_connections

Ingestion

imports, source_files, source_records, column_mappings, jobs

Commerce

orders, order_items, products, product_costs, returns

Marketplace ledger

settlements, settlement_lines, financial_transactions

Bank

bank_accounts, bank_transactions, settlement_bank_matches

Reconciliation

reconciliation_runs, reconciliation_matches, discrepancies

Tax & claims

tax_deductions, claims, claim_events

Governance & monetization

audit_events, subscriptions, usage_counters, ai_interactions

Rate rules

rate_cards, rate_card_rules, marketplace_policy_references

Database constraints and standards

Use NUMERIC(18,2) for INR ledger amounts and retain higher precision only where the rate calculation requires it.

Use TIMESTAMPTZ for event timestamps; preserve local business dates separately.

Enforce unique (workspace_id, sha256) for duplicate import detection.

Enforce unique (store_id, settlement_id) and stable order-line external keys.

Add tenant-leading composite indexes to all high-volume workspace queries.

Use foreign keys and explicit ON DELETE behaviour.

Use PostgreSQL Row-Level Security as defence-in-depth, in addition to application authorization.

Use Alembic migrations; do not call Base.metadata.create_all() during production startup.

Partition high-volume source records or settlement lines only when measured scale justifies it.

8. Security, privacy and compliance

SellerFlow AI will handle commercially sensitive financial data. Treat security as a P0 release gate.

Control

Required implementation

Authentication

Managed identity provider (e.g. Clerk or Supabase Auth) selected through an ADR; validate JWTs server-side.

Authorization

Workspace membership and role checks on every read/write; deny by default.

Tenant isolation

Tenant-scoped repositories and PostgreSQL RLS; automated cross-tenant tests.

File uploads

Generated storage keys; magic-byte/type validation; file-size, row and decompression limits; private storage; safe parsing.

Path safety

Never concatenate the user-supplied filename into a filesystem path.

Exports

Escape spreadsheet formula prefixes in every untrusted text cell, including tabs and carriage returns.

Secrets

Environment variables or secret manager; .env.example contains placeholders only.

Audit

Record imports, exports, manual matches, ledger adjustments, role changes and claim actions.

Privacy

Privacy notice, purpose limitation, retention/deletion workflow and breach response process.

AI processing

Mask customer PII, minimize data sent to providers, obtain appropriate consent and log model/prompt versions.

Operations

Rate limiting, CORS allowlist, security headers, dependency scanning, backups and restore tests.

Obtain qualified legal and tax review for DPDP Act obligations, GST TCS/TDS treatment, tax reporting language and any recovery-fee service. This blueprint is a product/engineering plan, not legal or tax advice.

9. AI strategy and guardrails

AI should reduce manual effort around a deterministic financial engine. It should not calculate financial totals, write ledger entries, invent evidence or file claims autonomously.

AI capability

Priority

Guardrail / implementation

Report recognition and column mapping

P1

Send headers and a small masked sample; return schema-constrained mapping suggestions; user confirms before saving.

Discrepancy explanation

P1

Ground explanation in computed discrepancy, source rows, rate-card rule and policy snippets; cite evidence.

Claim/dispute draft writer

P1

Draft only from verified facts; human reviews and copies/submits; record approval and outcome.

Anomaly detection

P2

Start with statistical baselines by SKU and fee type; alert only with evidence and thresholds.

Ask your books

P2

Read-only tenant-scoped semantic views; show data/query basis; never expose raw cross-tenant tables.

Policy change monitor

P2

Summarize official policy changes for human review; humans approve rate-card updates.

Autonomous claim filing

Not in scope

Do not automate submission in the initial product; marketplace terms and account-health risks require human control.

Use a provider abstraction so model providers can be changed without rewriting product logic.

Version prompts and models; maintain a regression evaluation set.

Track cost and usage by workspace.

Store AI interactions for audit with data minimization and retention controls.

If these capabilities are not delivered, avoid marketing claims that imply a live AI assistant.

10. Frontend and user experience

Split the current large page into route-level screens, feature modules and reusable UI components.

Use server-rendered marketing pages and authenticated app routes.

Replace hardcoded localhost API URLs with NEXT_PUBLIC_API_URL and environment-specific configuration.

Use typed API clients and remove any wherever practical.

Use server-side pagination and filtering for large order and transaction tables.

Display amounts using one INR formatter with lakh/crore grouping; financial totals must arrive as decimal strings.

Show real upload progress and job states; never simulate progress.

Provide empty, loading, error, permission and partial-data states on every major screen.

Use a mobile-first seller experience and dense desktop tables for accountants.

Meet WCAG 2.2 AA target: labels, keyboard navigation, focus management, contrast and non-colour-only status indicators.

Add Hindi first, then prioritize regional languages based on pilot demand.

Onboarding flow

Business setup → choose marketplace → guided report-download instructions → upload → import validation → first settlement/bank insight. Target time-to-first-reconciliation under five minutes, measured from a valid first upload to a useful, evidence-backed result.

Trust design

Every financial finding should expose its source, calculation, rule version and confidence state. Use Verified, Needs review and Informational labels. A “found money” banner is permitted only for a confirmed, evidence-backed amount; estimates and incomplete data must be visually distinct.

11. Testing, quality and release gates

Test layer

Required coverage

Release gate

Adapter golden files

Anonymized real Amazon settlement reports; later Flipkart and Meesho reports; headers, amounts, dates and row semantics.

Every supported report fixture passes expected normalized output.

Financial unit tests

Decimal arithmetic, rounding, rate-card boundaries, fee category matching, settlement totals and idempotency.

No float-based ledger calculations; reproducible outputs.

Property-based tests

Invariants such as line sums, reconciliation idempotency and no duplicate ledger writes.

Hypothesis suite passes.

API integration

PostgreSQL-backed import, reconciliation, bank match, tax and export workflows.

Migrations and API tests pass on PostgreSQL.

Security tests

User A cannot access user B's workspace, files, imports or exports; malicious upload names/types rejected.

Zero cross-tenant access in test suite.

Frontend component tests

Forms, status labels, error states, tables and accessible dialogs.

Vitest/RTL checks pass.

End-to-end

Sign up → create workspace → upload → reconcile → bank match → export.

Playwright smoke flow passes.

CI and dependency checks

ruff, mypy, pytest, ESLint, tsc, frontend tests, Playwright smoke, Docker build and dependency audit.

Required checks block merge.

Definition of financial correctness

No financial amount is fabricated to fill missing input.

Every posted value is traceable to source evidence.

Every rate calculation is tied to an effective-dated rule version.

Every reconciliation result is reproducible from stored inputs and versions.

Unknown or incomplete data is represented as Needs data, not silently converted to zero.

False-positive discrepancy rate is measured on a reviewed golden dataset and reported to pilot users.

12. Phased implementation roadmap

The schedule below is a planning sequence. It is not a delivery guarantee; actual duration depends on developer capacity, access to anonymized reports, product decisions and pilot feedback.

Phase

Indicative timing

Build scope

Exit criteria

P0 — Correctness & security

Weeks 1–2

Fix Amazon false positives; fix header normalization and amount parsing; remove synthetic values; persist dates; auth/tenant isolation; upload hardening; fix waterfall double counting; expand tests.

No fabricated numbers; cross-tenant tests pass; critical adapter cases covered.

P1 — Amazon financial core

Weeks 3–4

Amazon V2 settlement parser; canonical ledger; versioned rate-card engine; PostgreSQL/Alembic; async import pipeline; source evidence.

10 representative anonymized Amazon reports reconcile against independently prepared expected results.

P2 — Bank & tax

Weeks 5–6

Bank CSV import; settlement-to-bank matching; partial/delayed/unmatched credits; separate TDS/TCS records and monthly summary; core frontend routes.

Five pilot sellers complete a real month-end cycle with the tool.

P3 — Marketplace expansion & claims

Weeks 7–8

Flipkart adapter; Meesho upload adapter; returns/RTO reports; claim lifecycle; evidence-backed dispute drafts.

Every advertised adapter passes golden fixtures; claims trace to source evidence.

P4 — CA workspace & monetization

Weeks 9–10

Multi-client CA/agency workspace; roles; bulk exports; Tally mapping; Razorpay subscriptions and server-side usage metering.

One CA/agency completes a paid multi-client pilot.

P5 — AI & automation

Weeks 11–12+

AI column mapping; English/Hindi explanations; anomaly alerts; scheduled imports and provider integrations as justified.

AI reduces manual work in measured pilot tests without changing financial calculations.

Recommended first milestone: Financial Core v1

The next development milestone should be narrowly defined as: a securely authenticated seller uploads a real Amazon settlement report and a bank statement, sees the settlement components, sees whether the actual bank credit matches, and can investigate every difference with evidence. This is the first release that can credibly demonstrate the product's core promise.

13. Pricing hypotheses and monetization

The supplied research contains competitor price anchors, while the earlier development recommendation proposed a simpler initial hypothesis. Use pricing as an experiment, not as a settled market fact.

Plan hypothesis

Indicative price

Intended customer / scope

Free

₹0

Limited trial; one marketplace; small monthly order allowance; basic settlement summary.

Seller

₹499–₹799/month

Single seller; core reconciliation, fee audit, returns and accounting export.

Growth

₹1,499–₹2,499/month

Multi-channel seller; bank reconciliation, TDS/TCS, alerts and multiple users.

CA / Agency

₹3,999+/month

Multi-client workspace, role controls and bulk month-end exports; define client count and usage limits.

Recovery service add-on

10–15% of recovered amount (hypothesis)

Optional assisted claim workflow; validate legal, operational and marketplace-policy implications first.

Validate willingness to pay with paid pilots. Model infrastructure, support, file storage, AI usage, payment fees and professional services before finalizing margins. Enforce quotas server-side; do not rely on frontend-only limits.

14. Documentation and repository governance

Document / artifact

Required update

PRD.md

Update personas, positioning, fee-policy context, bank reconciliation, TDS/TCS, CA workflows and measurable outcomes.

TRD.md

Specify adapters, rate-card calculations, import jobs, row limits, performance targets and API contracts.

Architecture.md

Add current-vs-target architecture and ADRs for auth, queue, storage, hosting, AI and payments.

Database.md

Add new financial entities, constraints, indexes, RLS policy examples and migration strategy.

API.md

Regenerate from OpenAPI; document auth, pagination, error model, async imports, idempotency and jobs.

Integration.md

Document each marketplace report type, download instructions, API access limitations and fixture coverage.

Authentication.md / Security.md

Define provider, roles, tenant checks, file hardening, privacy, audit and AI consent.

UI_UX.md / Design.md

Document onboarding, status vocabulary, evidence presentation, accessibility and responsive behaviour.

Testing_and_QA.md

Add golden files, property-based tests, tenant isolation, PostgreSQL integration and CI gates.

DEVELOPED_FEATURES.md

Replace broad completion claims with Implemented / Partial / Prototype / Planned / Tested / Pilot-ready.

New: FINANCIAL_DOMAIN_MODEL.md

Define transaction types, dates, money semantics, evidence and reconciliation invariants.

New: RECONCILIATION_RULES.md and RateCards.md

Document matching logic, tolerances, effective dates, sources, review and versioning.

New: Market_Analysis.md and Pricing.md

Keep market assumptions, source dates, competitor claims and pricing experiments auditable.

New: PILOT_VALIDATION.md and RELEASE_CHECKLIST.md

Record pilot evidence, acceptance results, known limitations and go/no-go approvals.

New: ADR/ and CHANGELOG.md

Record consequential technical choices and product/ruleset changes.

Engineering governance rules

Use small, reviewable pull requests instead of a single large implementation commit.

Every feature must include tests at the correct layer and update relevant documentation.

An AI coding agent or developer may not mark an adapter complete until its golden-file fixtures pass.

Never mark a feature “verified” based only on UI appearance or a successful mock response.

Keep demo data visibly labelled and separate from real customer workspaces.

Pin dependencies with a lockfile and align documented versions with actual package manifests.

15. Success metrics and pilot scorecard

Metric

Definition / purpose

Initial measurement approach

Time to first reconciliation

Time from first valid upload to first useful evidence-backed result.

Track per onboarding session; target under 5 minutes.

Discrepancy precision

Share of flagged discrepancies confirmed as valid by seller/CA review.

Label a reviewed sample; optimize precision before recall.

Unexplained balance

Amount remaining unmatched after a reconciliation cycle.

Track amount and age; do not hide unresolved items.

Claim conversion

Share of drafted/filed claims that are approved and received.

Track lifecycle and amounts separately.

Month-end time saved

Change in time required to close a seller's marketplace books.

Before/after pilot time logs.

Week-4 retention

Share of activated accounts still using the product in week four.

Cohort analysis after pilot launch.

Paid conversion

Free/ pilot accounts converting to paid plan.

Measure by segment and acquisition channel.

Support burden

Manual support time per import or month-end close.

Track reasons: file format, mapping, fee rule, bank match.

Pilot go/no-go

Do not launch broad paid acquisition until: (1) tenant isolation and upload security pass; (2) Amazon golden files pass; (3) a real bank statement can be matched without inferred values; (4) a CA or seller validates the explanations; and (5) limitations and supported report formats are documented.

16. Key decisions still requiring confirmation

Decision

Options / question

Recommended approach

Identity provider

Clerk vs Supabase Auth vs other managed provider.

Choose through a short ADR based on Next.js/FastAPI integration, cost, roles and data handling.

Hosting and data region

Vercel + Railway/Render/Fly.io, AWS Mumbai or alternatives.

Compare total cost, reliability, backups, data location and operational burden.

Queue and worker

RQ, Celery, Arq, Dramatiq or managed alternative.

Choose the simplest Redis-backed worker that meets retry and observability needs.

Object storage

S3, R2 or compatible provider.

Private bucket, encryption, presigned access, retention and deletion.

Bank formats

Which bank statement formats are required in pilot?

Start with the actual banks used by pilot sellers; avoid claiming universal support.

Rate-card governance

Who sources, reviews and publishes fee changes?

Require source URL/document, effective date, reviewer and versioned release.

Tax review

Which professional validates TDS/TCS treatment and reports?

Obtain qualified CA/legal review before production tax features.

Pricing and quotas

How many orders, stores, users and clients per tier?

Run paid pilots and measure actual cost-to-serve.

17. Final recommendation

Build trust before breadth. First secure the product and make Amazon settlement-to-bank reconciliation correct, evidence-backed and repeatable. Then add TDS/TCS and CA workflows, followed by validated marketplace adapters and carefully governed AI assistance.

The immediate engineering objective is not “finish all features.” It is to deliver one complete financial workflow that a seller or CA can trust at month-end. That workflow becomes the foundation for marketplace expansion, paid plans and defensible product differentiation.

Appendix A — Source and confidence notes

Primary supplied source: “SellerFlow AI — Senior Product & Engineering Review”, dated 17 November 2026, covering repository commit ca389d5, market analysis, code review, test-fixture observations, architecture, security and roadmap. The report states that its author cloned the repository, inspected documentation and code, and ran the adapters and reconciliation engine against included fixtures. This document reproduces those findings as reported; it does not certify that the repository was independently re-run during document generation.

Market sources named in the supplied review include IBEF, Business Standard reporting on Bain/Flipkart, JM Financial, Economic Times, Amazon fee schedules and SP-API documentation, competitor vendor pages, and secondary market summaries. Before relying on any market size, fee schedule, tax rate, API availability, competitor price or product claim, revisit the original source and record the date checked.

The serviceable account estimate, pricing bands, timeline and proposed success metrics are planning hypotheses. Validate them through interviews, real anonymized report fixtures, pilot usage and paid conversion.

Appendix B — Suggested implementation ticket sequence

ID

Workstream

Ticket scope

Acceptance criteria

SF-001

Security baseline

Add authentication middleware, workspace membership checks and tenant-scoped repository access.

Cross-tenant API tests; unauthenticated protected requests return 401/403.

SF-002

Upload hardening

Replace user-controlled paths with generated object keys; validate type, size and row limits.

Traversal and invalid-file tests pass.

SF-003

Financial date persistence

Persist marketplace dates and return/refund dates as typed fields.

Fixture tests prove source dates survive parse → ledger → API.

SF-004

Adapter header normalization

Normalize case, spaces, underscores and hyphens; fix Flipkart/Meesho mapping tests.

Real fixtures yield non-zero expected rows and correct dates.

SF-005

Amazon settlement V2 parser

Parse settlement header and amount-type/description transaction semantics.

Golden files reproduce independently calculated settlement totals.

SF-006

Canonical ledger

Represent sales, fees, refunds, reserves, adjustments, TDS and TCS distinctly.

Ledger invariants and provenance tests pass.

SF-007

Rate-card engine

Implement effective-dated fee rules and category-specific expected fee calculation.

Boundary, versioning and tolerance tests pass.

SF-008

Reconciliation engine

Match like-for-like financial categories; remove gross-vs-net false positives.

Known normal-fee fixture creates no false overcharge.

SF-009

PostgreSQL migrations

Introduce PostgreSQL schema, constraints, indexes and Alembic migrations.

Fresh database upgrade/downgrade tests pass.

SF-010

Async import jobs

Return 202 + import_id; process parsing and reconciliation in worker.

Retry/idempotency and job status tests pass.

SF-011

Bank statement import

Add configurable bank CSV parsers and normalized bank transactions.

Sample statement rows and totals match expected output.

SF-012

Settlement-bank matching

Match by reference, amount and date window; support manual review.

Partial, delayed and unmatched cases are correctly represented.

SF-013

Tax deductions

Add separate TDS/TCS records and monthly summaries.

CA-reviewed fixtures reconcile to source tax records.

SF-014

Evidence UI

Show source rows, formulas, rate-card version and status for every exception.

A reviewer can reproduce each displayed result.

SF-015

Exports

Add CSV/XLSX and configurable Tally XML mappings.

Export totals tie to selected ledger period; formula injection tests pass.

SF-016

Pilot instrumentation

Track activation, discrepancy precision, close time, claim outcomes and retention.

Pilot scorecard populated from real events.

Confidential working document  •  17 November 2026  •  