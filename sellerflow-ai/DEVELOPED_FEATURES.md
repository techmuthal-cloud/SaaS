# SellerFlow AI — Developed Features & Technical Architecture Manifest

> **Product:** Financial operations and multi-marketplace settlement reconciliation workspace for Indian e-commerce sellers.  
> **Status:** Full Free-Tier SaaS Implementation Complete & Verified Live.  
> **Current Version:** `v1.2.0-free-tier`  
> **Repository Root:** `c:\Users\Lenovo\Downloads\SellerFlow_AI_Documentation\sellerflow-ai`

---

## 1. Executive Summary & Problem Solved

Marketplace sellers in India (Amazon, Flipkart, Meesho) face massive operational leakage:
1. Reconciling by arbitrary calendar months creates artificial date-cutoff gaps.
2. Marketplaces pay on overlapping 7-to-14 day disbursement cycles with rolling account reserves.
3. Every platform invents different names for the same fee types.
4. Sellers leave thousands of rupees unclaimed in unreturned customer refunds (45-day window) and volumetric weight slab overcharges.

**SellerFlow AI** provides an end-to-end deterministic financial workspace that normalizes raw settlement statements, reconciles bank NEFT deposits, flags fee overcharges, generates 1-click dispute tickets, tracks cohort return losses, and outputs TallyPrime accounting vouchers.

---

## 2. Complete List of Developed Features

### Core P0 Features (Initial MVP)
- [x] **Multi-Tenant Workspaces & Stores:** Multi-tenant workspace management supporting individual stores for Amazon India, Flipkart, and Meesho.
- [x] **Safe File Ingestion Pipeline:** Accepts CSV, TSV, TXT, and XLSX files up to 25MB with SHA-256 deduplication and mime/header checks.
- [x] **Deterministic Reconciliation Engine:** 100% rule-based matching using Python `decimal.Decimal` (zero floating-point math, zero LLM guesswork).
- [x] **Free-Tier Usage Quota:** Built-in tracking of up to 10,000 reconciled orders/month per workspace.
- [x] **Product Unit Economics & Profitability:** SKU-level input for COGS, packaging, and shipping estimates; explicitly tracks missing costs rather than assuming ₹0.
- [x] **Formula-Escaped Reconciliation Export:** Downloadable CSV reconciliation report with formula injection sanitization (`=`, `+`, `-`, `@`).

### High-Impact Advancements
- [x] **Auto-Generated 1-Click Dispute Package Generator:**
  - Instantly crafts copy-pasteable claims for Seller Support / Helpdesk with formal subjects, policy citations, exact order references, and attached CSV calculation proofs.
  - Handles **Fee & Weight Slab Overcharges**, **Missing Payouts**, and **Amazon SAFE-T / Flipkart SPF Claims**.
- [x] **Multi-Marketplace Adapters (Flipkart & Meesho):**
  - **Flipkart Adapter:** Normalizes Flipkart `Payment_Report` and `Sales_Report` (Pick & Pack fees, commission slabs, fixed fees).
  - **Meesho Adapter:** Ingests Meesho zero-commission supplier payment statements and COD deductions.
  - **Unified Multi-Store View:** Header dropdown enables toggling between unified view across all stores or filtering into a single marketplace.
- [x] **RTO & Customer Return Leakage Detector (>45 Days):**
  - Audits customer refunds against return windows.
  - Flags unreturned refunds where physical inventory was never restocked or compensated after 45 days.

### Real-World Seller Validation Advancements
- [x] **Settlement-Period & Reserve Tracking Recon (`/settlement-cycle-recon`):**
  - Reconciles by exact marketplace disbursement cycle (Settlement ID) rather than calendar months.
  - Reconciles: `Gross Sales - Referral - Closing - Shipping - Refunds - Current Reserve Held + Previous Reserve Released = Bank NEFT Deposit`.
- [x] **Universal Multi-Marketplace Stacked Pivot Matrix (`/multi-marketplace-pivot`):**
  - Maps differing platform labels into unified canonical fee buckets:
    - *Gross Order Sales*
    - *Referral / Commission Fee*
    - *Fixed Closing Fee*
    - *Fulfillment & Shipping Fee*
    - *Customer Returns Debited*
    - *Account Reserve Held*
    - *Previous Reserve Released*
    - *Ad Spend Deductions*
    - *Net Settlement Payout*
- [x] **Cohort-Based Return Attribution (`/cohort-returns`):**
  - Attributes delayed customer refunds back to the **original order date and SKU** to protect current-period margins and highlight high-defect products (>15% return rate).

### UI/UX, Interaction & Growth Features
- [x] **Interactive Financial Settlement Waterfall:** Visual Recharts bar visualization showing money flow from Gross Revenue down to Net Bank Payout.
- [x] **Slide-Over Evidence Drawer:** Clickable eye icon on any order opening a right-side drawer with exact raw JSON payloads, row numbers, and audit comparisons.
- [x] **Smart Search & Quick Filter Bar:** Filter by Order ID, issue keywords, and severity thresholds (`High Severity > ₹100`).
- [x] **Batch Dispute Manifest:** Multi-order checkbox selection with 1-click batch CSV manifest export.
- [x] **TallyPrime XML Journal Exporter:** Generates ready-to-import XML DayBook vouchers debiting bank and expense ledgers and crediting sales.
- [x] **"Found Money" High-ROI Banner:** Highlights total discoverable claim amounts in ₹ right when the seller logs in.
- [x] **Public Landing & Marketing Home Page:** High-converting landing section featuring logistics/delivery warehouse imagery, value proposition, metric cards, and a 4-step "How It Works" guide.

---

## 3. Technology Stack & Development Requirements

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Web Frontend** | **Next.js (App Router)** | `16.4.6` | High-performance React application shell |
| **UI Library** | **React** | `19.3.0` | Declarative UI state management |
| **Language** | **TypeScript** | `5.x` | End-to-end type safety between frontend and contracts |
| **Styling** | **Tailwind CSS** | `4.3.3` | Utility-first, responsive, financial styling tokens |
| **Icons** | **Lucide React** | `^1.16.0` | Accessible vector icon set |
| **Charts** | **Recharts** | `^2.15.1` | Financial waterfall and money-flow SVG charts |
| **Backend API** | **FastAPI** | `0.133.1` | Asynchronous REST API with auto OpenAPI Swagger documentation |
| **ASGI Server** | **Uvicorn** | `0.41.0` | Production ASGI web server |
| **Validation** | **Pydantic / Pydantic Settings** | `2.13.4` | Request/response schema validation |
| **Database & ORM**| **SQLAlchemy** | `2.1.8` | Relational ORM with transaction support |
| **Database** | **SQLite (Dev) / PostgreSQL (Prod)** | Standard | System of record with tenant-isolated queries |
| **Data Parsers** | **openpyxl, polars, csv** | `3.1.5` / `2.1.0` | Fast memory-safe parsing of Excel and delimited files |
| **Financial Math** | **Python `decimal.Decimal`** | Built-in | **Deterministic financial arithmetic** with zero binary float drift |
| **Accounting** | **Tally XML Format** | Custom Service | Native journal voucher integration for TallyPrime |
| **Testing** | **Pytest** | `9.2.0` | Automated test suite for matching rules and fixtures |

---

## 4. Repository File Structure

```text
sellerflow-ai/
├── DEVELOPED_FEATURES.md      # <--- This document
├── apps/
│   ├── api/                   # Python FastAPI Backend
│   │   ├── app/
│   │   │   ├── core/          # config.py, database.py
│   │   │   ├── models/        # entities.py (Workspaces, Stores, Imports, Transactions)
│   │   │   ├── routes/        # api_v1.py (All REST endpoints)
│   │   │   ├── services/      # amazon_adapter.py, multimarketplace_adapters.py,
│   │   │   │                  # reconciliation_engine.py, dispute_generator.py,
│   │   │   │                  # return_leakage_service.py, tally_exporter.py,
│   │   │   │                  # settlement_cycle_service.py, multi_marketplace_pivot_service.py,
│   │   │   │                  # cohort_return_service.py
│   │   │   └── main.py        # FastAPI entrypoint
│   │   └── requirements.txt   # Python backend dependencies
│   └── web/                   # Next.js Frontend
│       ├── src/app/
│       │   ├── page.tsx        # Main application dashboard (Workspace + Tab routing)
│       │   ├── LandingHome.tsx # Public Landing page with delivery background & "How it works"
│       │   ├── layout.tsx      # Root layout
│       │   └── globals.css     # Tailwind styles
│       ├── package.json        # Frontend dependencies
│       └── tsconfig.json       # TypeScript configuration
├── tests/
│   ├── fixtures/              # sample_amazon_settlement.tsv, sample_flipkart_settlement.csv, sample_meesho_settlement.csv
│   └── test_reconciliation.py # Automated Pytest test suite
└── storage/
    └── uploads/               # Private encrypted storage for ingested settlement reports
```

---

## 5. Live Services & Verification Commands

### 1. Web Application
- **URL:** [http://localhost:3000](http://localhost:3000)
- **Features available to test:**
  - Landing Home section with logistics background and "How It Works".
  - One-click switch to the **Live Seller Workspace**.
  - Interactive Recharts **Settlement Waterfall**.
  - **Settlement Period & Reserves** bank deposit matching.
  - **Multi-Marketplace Stacked Pivot** (Amazon vs. Flipkart vs. Meesho).
  - **Cohort Return Attribution** (Order Date vs. Settlement Date).
  - **Discrepancies & Claims** with 1-Click Dispute Generator and Batch Manifest Export.
  - **Slide-Over Evidence Drawer** for inspecting raw payload rows.
  - **TallyPrime XML Voucher Export**.

### 2. Backend REST API & OpenAPI Docs
- **Swagger Documentation:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Health Endpoint:** [http://localhost:8000/](http://localhost:8000/)

### 3. Running Automated Tests
```powershell
$env:PYTHONPATH="c:\Users\Lenovo\Downloads\SellerFlow_AI_Documentation\sellerflow-ai\apps\api"
pytest c:\Users\Lenovo\Downloads\SellerFlow_AI_Documentation\sellerflow-ai\tests\test_reconciliation.py
```
*(All tests passing 100%).*
