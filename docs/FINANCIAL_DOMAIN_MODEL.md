# SellerFlow AI — Financial Domain Model & Calculation Rules

Version 2.0 | November 2026

## 1. Core Principles of Financial Integrity
1. **Deterministic Arithmetic Only**: Zero floating-point arithmetic. Every financial calculation is executed strictly using `decimal.Decimal` in Python and `NUMERIC(18, 2)` in PostgreSQL.
2. **AI Never Alters Ledger Values**: LLMs and AI assist with explanations, column mapping recommendations, and dispute ticket drafts, but are strictly prohibited from mutating or calculating ledger values.
3. **No Phantom Claims**: A difference between gross selling price and net settlement payout is **not** an overcharge; it represents standard contracted marketplace deductions.
4. **Like-for-Like Fee Audit**: Rate card rules calculate the *expected* fee for the SKU's category, price band, and weight slab. The expected fee is compared strictly against the corresponding actual fee deduction line(s).
5. **Traceable Provenance**: Every normalized transaction, discrepancy, and match retains its `workspace_id`, `import_id`, `source_row_number`, and rate card version.

---

## 2. Three Distinct Financial Views
Financial clarity requires separating three distinct operational timelines:

| Financial View | Business Question Answered | Primary Ledger Entities |
|---|---|---|
| **1. Order Economics** | What was sold, what did the customer pay, and what was product COGS? | `orders`, `order_items`, `products`, `returns` |
| **2. Marketplace Earnings** | What did Amazon/Flipkart/Meesho charge, withhold in reserves, or disburse? | `settlements`, `settlement_transactions`, `rate_cards` |
| **3. Cash Movement** | What exact funds entered or left the seller's commercial bank account? | `bank_accounts`, `bank_transactions`, `settlement_bank_matches` |

---

## 3. Discrepancy Vocabulary
A discrepancy is an **investigation record**, not a cash transaction. It must never be subtracted directly from a bank payout waterfall.

* `matched`: Actual fee matches rate card expected fee within tolerance (+/- ₹1.00).
* `short_paid`: Marketplace actual net disbursement is lower than rate card contracted payout.
* `over_paid`: Marketplace disbursed more than expected; flagged for classification review.
* `pending_reserve`: Funds are explicitly held in unavailable balance (e.g., A-to-z claim reserve).
* `missing`: Expected order payout is completely absent from the disbursement cycle.
* `needs_data`: Incomplete report attributes prevent rate card determination; never assumed zero.

---

## 4. Statutory Tax Withholdings (India)
1. **Section 194-O TDS (Income Tax)**: 1% deducted by marketplace operators on gross e-commerce sales.
2. **Section 52 GST TCS**: 1% (0.5% CGST + 0.5% SGST or 1% IGST) collected by e-commerce operators at source.
Tax withholdings are tracked distinctly from commercial fees to enable chartered accountants to reconcile 26AS/AIS and GSTR-8 effortlessly.
