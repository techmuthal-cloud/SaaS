# SellerFlow AI

> Financial operations and reconciliation workspace for e-commerce sellers.

SellerFlow AI is a proposed SaaS product that helps marketplace sellers import financial reports, reconcile orders and settlements, investigate discrepancies, and understand product-level profitability. The product is designed to make financial workflows explainable and auditable—not to replace accounting professionals or statutory tax systems.

## Documentation index

| Document | Purpose |
|---|---|
| [PRD.md](PRD.md) | Product vision, users, goals, scope, requirements and success metrics |
| [TRD.md](TRD.md) | Technical requirements, constraints and non-functional targets |
| [Design.md](Design.md) | Product design principles, information architecture and interaction patterns |
| [UI_UX.md](UI_UX.md) | Screen-by-screen UX and component specifications |
| [Architecture.md](Architecture.md) | System architecture, services, deployment and data flow |
| [Database.md](Database.md) | PostgreSQL schema, relationships, tenancy and indexing |
| [API.md](API.md) | REST API conventions, endpoints, request/response examples |
| [Authentication.md](Authentication.md) | Identity, sessions, authorization and account lifecycle |
| [Security.md](Security.md) | Threat model, security controls, privacy and retention |
| [Integration.md](Integration.md) | Marketplace and third-party integration strategy |
| [MCPConnection.md](MCPConnection.md) | Safe use of MCP-connected developer tools and external context |
| [Agents.md](Agents.md) | AI coding-agent roles, boundaries and handoff rules |
| [FeatureDevelopment.md](FeatureDevelopment.md) | Feature workflow, acceptance criteria and release gates |
| [ProjectImplementation.md](ProjectImplementation.md) | Phased implementation plan and work breakdown |
| [Setup.md](Setup.md) | Local development environment setup |
| [Testing_and_QA.md](Testing_and_QA.md) | Test strategy, fixtures and release QA |
| [Debugging.md](Debugging.md) | Diagnostics, logs and common failure playbooks |
| [AppFlow.md](AppFlow.md) | User journeys and application state flows |
| [Rules.md](Rules.md) | Product, engineering, data and AI guardrails |
| [Tools.md](Tools.md) | Approved tools, libraries and operational services |

> Filename note: `ProjectImplementation.md` corrects the spelling in the original request. `Testing_and_QA.md` uses underscores so it is portable across operating systems and command-line tools.

## Current product definition

**Primary promise:** Help sellers understand what they should have received, what they actually received, where differences exist, and how marketplace costs affect real product profitability.

**Initial target market:** Small and growing e-commerce sellers operating in India. Initial supported marketplace workflow is to be selected after customer interviews and sample-file validation. The architecture must support multiple marketplace adapters, but no marketplace API, file format, or automated connection should be advertised as supported until it has passed the Integration Readiness Checklist.

**MVP workflow:**

1. Create a business and store profile.
2. Upload supported order, settlement/payment and optional cost reports.
3. Detect file type, validate columns and map fields.
4. Normalize records into a canonical internal model.
5. Match orders, fees, refunds and payouts using documented rules.
6. Flag unresolved differences with source-record traceability.
7. Review SKU/order profitability using user-supplied cost inputs.
8. Export a reconciliation report.

## Important assumptions and limits

- All marketplace integrations are adapter-based. Actual API access, partner approval, OAuth scopes, rate limits and report formats must be verified against current official marketplace documentation before implementation.
- The first release may use manual CSV/XLSX uploads. This is a deliberate way to validate the financial workflow before investing in automated integrations.
- AI can assist with file classification, column-mapping suggestions and explanations. It must never be the source of truth for financial arithmetic or silently invent transaction matches.
- The product provides operational financial analysis and report preparation. It does not provide certified accounting, audit, tax, legal or investment advice.
- Tax-related outputs must be labelled as estimates or preparation aids unless reviewed and approved by qualified professionals.
- Competitor observations are hypotheses for product differentiation, not proof of competitor defects or guaranteed customer switching demand.

## Recommended repository layout

```text
sellerflow-ai/
├── apps/
│   ├── web/                 # Next.js frontend
│   └── api/                 # FastAPI HTTP application
├── workers/
│   └── jobs/                # Async file-processing workers
├── packages/
│   ├── contracts/           # Shared API schemas / generated types
│   └── ui/                  # Shared UI components (optional)
├── docs/                    # This documentation set
├── infra/                   # Docker, deployment and IaC configuration
├── scripts/                 # Dev and maintenance scripts
├── tests/                   # Cross-service tests and fixtures
├── .env.example
└── README.md
```

## Build philosophy

Ship one accurate and explainable reconciliation workflow before broadening feature scope. Prefer explicit rules, source references, repeatable imports, idempotent processing, tenant isolation and measurable confidence over opaque automation.
