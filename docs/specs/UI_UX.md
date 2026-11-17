# UI/UX Specification

## 1. Application shell

- Left navigation rail/sidebar on desktop.
- Workspace and store selector at the top.
- Global period selector where applicable.
- Main content region with breadcrumb, page title and primary action.
- Notification/help/profile controls in header.
- Responsive collapse to a compact navigation pattern on small screens.

## 2. Public website pages

### Home
- Hero: “Know where every rupee goes.”
- Subheading describing settlement reconciliation and product profitability.
- Primary CTA: Try sample demo.
- Secondary CTA: Explore how it works.
- Product screenshot using clearly labelled sample data.
- Workflow explanation: Import → Reconcile → Investigate → Analyse.
- Supported integrations list with support status.
- Security and data handling summary.
- Pricing and FAQ.

### Features
Separate pages/sections for reconciliation, discrepancy investigation, profitability, reporting and accountant workspace. Avoid claims that are not shipped.

### Integrations
Show each connector's support status: Available, Limited, Beta, Planned or Not supported. Explain whether it uses file upload, API, extension or another permitted method.

### Pricing
Show plan price, billing period, GST/tax treatment where applicable, usage limits, included features, overage policy, cancellation and refund terms.

### Security
Explain storage, encryption, tenant access, retention, deletion and subprocessors accurately. Do not claim certifications unless obtained.

## 3. Authenticated screens

| Screen | Key elements | Primary action |
|---|---|---|
| Dashboard | Period, metrics, import status, attention queue | Upload report |
| Onboarding | Business profile, store, marketplace choice | Create workspace |
| Upload Centre | Dropzone, file rules, templates | Upload files |
| Import Detail | Status timeline, validation summary, row errors | Confirm mapping / retry |
| Mapping Studio | Source columns, canonical fields, sample values | Save mapping |
| Import History | File, marketplace, period, status, actor | Open import |
| Reconciliation | Summary cards, matches, exceptions, filters | Investigate exceptions |
| Discrepancy Detail | Difference, source rows, rule, notes, review state | Mark reviewed |
| Transaction Explorer | Search, filters, source lineage | Open record |
| Profitability | Product, revenue, costs, margin, data completeness | Edit costs |
| Cost Setup | COGS, packaging, shipping assumptions, ad cost source | Save cost profile |
| Reports | Templates, periods, formats, generation status | Generate export |
| AI Assistant | Suggested questions, answer with citations to internal records | Ask question |
| Stores & Integrations | Store connection, import modes, permissions | Add connection |
| Team / Clients | Members, roles, client workspaces | Invite member |
| Notifications | Import failures, discrepancies, system messages | Open item |
| Billing | Plan, usage, invoices, payment status | Manage plan |
| Security Settings | Sessions, data retention, deletion request | Save controls |
| Workspace Settings | Name, timezone, currency, preferences | Save settings |

## 4. Critical workflows

### Upload workflow
1. User selects a store and reporting period.
2. User uploads one or more files.
3. Client and server validate size, extension and content signature.
4. Import record is created; UI shows queued/processing state.
5. Worker detects report type and schema.
6. If confidence is insufficient, user is routed to mapping studio.
7. User confirms mapping.
8. Worker normalizes and validates rows.
9. UI displays accepted, rejected and warning counts.
10. User opens reconciliation result.

### Discrepancy workflow
1. User opens a flagged difference.
2. UI shows type, amount, period and status.
3. UI displays matched and unmatched source records.
4. User reviews rule and calculation detail.
5. User adds note or marks for follow-up.
6. Every change is recorded in audit history.

### Profitability workflow
1. User chooses period/store/SKU.
2. System calculates revenue and available cost components.
3. Missing costs are identified separately.
4. User enters or imports missing cost data.
5. System recalculates using a versioned rule.
6. UI labels results as complete or partial based on cost coverage.

## 5. Data table requirements

- Server-side pagination for large data sets.
- Search and filters must be tenant-scoped.
- Amount columns show currency code/symbol consistently.
- Negative amounts use a clear sign and accessible label.
- Export respects the active filters or asks the user which scope to export.
- Row detail includes source file, sheet and row number.
- Do not render untrusted cell content as HTML.

## 6. Status model and copy

| Status | Meaning | Suggested label |
|---|---|---|
| queued | Waiting for worker | Queued |
| validating | Checking file and schema | Validating |
| needs_mapping | User input required | Needs mapping |
| processing | Normalizing/matching | Processing |
| completed | Process finished with no blocking errors | Completed |
| completed_with_warnings | Usable output has warnings | Completed with warnings |
| failed | Processing cannot continue | Failed |
| matched | Records matched under rule | Matched |
| partial | Only part of expected amount/records matched | Partially matched |
| unmatched | No eligible match found | Unmatched |
| ambiguous | More than one plausible match | Ambiguous |

## 7. Accessibility

Target WCAG 2.2 AA for core journeys. Use semantic headings, associated labels, keyboard-operable controls, visible focus, screen-reader status updates, accessible charts and non-colour status text.
