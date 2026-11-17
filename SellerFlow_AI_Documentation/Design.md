# Product Design

## 1. Design direction

SellerFlow AI should feel like a reliable financial operations tool: calm, precise, readable and transparent. It should not resemble a trading terminal or overly decorative AI dashboard.

### Experience principles
- **Clarity over density:** show totals and next actions before large tables.
- **Explain every status:** use words and supporting detail, not colour alone.
- **Traceability by default:** every number should be inspectable.
- **Progressive disclosure:** show essential information first; expose formulas and raw rows on demand.
- **Safe actions:** confirm destructive actions and explain their effects.
- **Consistent empty states:** every empty page tells the user what is missing and how to proceed.

## 2. Visual identity direction

Suggested direction: premium SaaS with a light neutral canvas, deep navy text, muted slate surfaces and a restrained green accent for verified/success states. Use amber for needs-review and red for errors or confirmed negative outcomes. Do not use colour as the only status indicator.

### Suggested design tokens

| Token | Suggested value | Usage |
|---|---|---|
| Background | `#F7F8FA` | Main application canvas |
| Surface | `#FFFFFF` | Cards and tables |
| Text primary | `#172033` | Main text |
| Text secondary | `#64748B` | Supporting copy |
| Border | `#E2E8F0` | Dividers and outlines |
| Brand navy | `#172B4D` | Navigation and important controls |
| Accent green | `#16865A` | Verified/positive states |
| Warning amber | `#B7791F` | Needs review |
| Error red | `#C2413B` | Failed or confirmed issue |

Treat tokens as a starting point and validate contrast in the implemented theme.

## 3. Information architecture

Primary navigation:
1. Overview
2. Imports
3. Reconciliation
4. Discrepancies
5. Profitability
6. Reports
7. Stores & integrations
8. Team / Clients (role-dependent)
9. Settings

Utility navigation: notifications, help, workspace switcher, profile and billing.

## 4. Dashboard hierarchy

The dashboard should answer, in order:
1. What period and workspace am I viewing?
2. Did the latest import complete?
3. What is the settlement and reconciliation status?
4. Which differences need attention?
5. What is known about profit and which costs are missing?
6. What action should I take next?

Do not combine incompatible periods or currencies in one total without explicit conversion and disclosure.

## 5. Interaction patterns

- Use tables for transaction-level detail; support column selection, sorting, filtering and sticky headers.
- Use side panels or detail pages for discrepancy investigation.
- Provide source row navigation from normalized record to original file/sheet/row.
- Use status labels: `Matched`, `Partially matched`, `Unmatched`, `Ambiguous`, `Needs review`, `Failed`.
- Use skeletons for loading, not fake zero values.
- Show timestamps with timezone context where relevant.
- Confirm reprocessing when it may create a new calculation version.
- Make export configuration clear before download.

## 6. Responsive behaviour

Desktop is the primary environment for spreadsheet-heavy workflows. Tablet should support review and approvals. Mobile should support dashboard glance, notifications and issue review; do not force wide financial tables into unreadable mobile layouts. Provide responsive table cards or horizontal scrolling with preserved row labels.

## 7. Content design

Use plain, precise language. Examples:
- Prefer: “₹250 difference — 2 source records need review.”
- Avoid: “AI found a hidden loss.”
- Prefer: “Possible shipping fee mismatch; confirm against marketplace statement.”
- Avoid: “Marketplace incorrectly charged you” unless the evidence proves it.

## 8. Design quality checklist

- Every page has title, purpose and primary action.
- Empty, loading, error, partial and success states are designed.
- Keyboard focus is visible.
- Forms have labels, validation and helpful error copy.
- Charts include text alternatives or accessible tables.
- Colour contrast meets target accessibility standards.
- Data tables have meaningful column headers and units.
- Destructive operations require confirmation.
