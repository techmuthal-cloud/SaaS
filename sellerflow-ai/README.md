# SellerFlow AI

> **Financial operations and multi-marketplace settlement reconciliation workspace for e-commerce sellers (Amazon India, Flipkart, Meesho).**

---

## 📖 Quick Links
- **Comprehensive Manifest of Shipped Features & Tech Details:** [DEVELOPED_FEATURES.md](DEVELOPED_FEATURES.md)
- **Product Requirements Document:** [../SellerFlow_AI_Documentation/PRD.md](../SellerFlow_AI_Documentation/PRD.md)
- **Technical Architecture:** [../SellerFlow_AI_Documentation/Architecture.md](../SellerFlow_AI_Documentation/Architecture.md)

---

## 🚀 Running the Application Locally

### 1. Backend Service (FastAPI)
```powershell
cd apps/api
$env:PYTHONPATH="."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs & Swagger UI: **http://localhost:8000/api/v1/docs**

### 2. Frontend Application (Next.js)
```powershell
cd apps/web
npm install
npm run dev -- -p 3000
```
- Web Application: **http://localhost:3000**

### 3. Running Automated Tests
```powershell
$env:PYTHONPATH="apps/api"
pytest tests/test_reconciliation.py
```

---

## 🛠️ Developed Features Summary
- **Multi-Marketplace Ingestion:** Amazon India (`.tsv`/`.csv`/`.xlsx`), Flipkart (`Payment_Report`), Meesho Supplier Sheets.
- **Settlement-Period Recon:** Reconciles exact disbursement cycles against Bank NEFT deposits with rolling reserve release tracking.
- **Universal Multi-Store Pivot:** Stacks Amazon, Flipkart, and Meesho side-by-side using standardized canonical fee categories.
- **1-Click Dispute Ticket Generator:** Formats ready-to-paste claims with calculations and CSV evidence for Amazon SAFE-T and Flipkart Support.
- **Cohort Return Linking:** Connects delayed refunds back to the original order date and SKU to protect period margins.
- **RTO & Return Leakage Tracker:** Flags customer refunds older than 45 days where inventory was never restocked.
- **TallyPrime XML Export:** 1-click XML DayBook voucher download for direct import into Tally.
- **Landing Page with Logistics Background & "How It Works" Section:** Converts incoming sellers with a 4-step workflow breakdown.
