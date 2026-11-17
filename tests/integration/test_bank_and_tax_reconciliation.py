import io
import pytest
from decimal import Decimal
from app.services.bank_statement_service import BankStatementService
from app.services.tax_reconciliation_service import TaxReconciliationService

def test_bank_statement_csv_parsing():
    sample_bank_csv = """Txn Date,Description,Ref No,Debit,Credit,Balance
2026-11-05,AMAZON DISBURSEMENT SETTLE-001,UTR1029192,,125000.00,450000.00
2026-11-06,OFFICE RENT EXPENSE,,25000.00,,425000.00
2026-11-07,FLIPKART INTERNET PAYMENT,UTR882910,,84500.00,509500.00
"""
    parsed = BankStatementService.parse_csv(io.StringIO(sample_bank_csv))
    assert len(parsed) == 3
    # Check first credit transaction
    first = parsed[0]
    assert first["credit_amount"] == Decimal("125000.00")
    assert "AMAZON DISBURSEMENT" in first["narration"]
    assert first["reference_number"] == "UTR1029192"

def test_settlement_to_bank_match():
    bank_txns = [
        {"narration": "NEFT SETTLE-AMZ-NOV-A DEPOSIT", "reference_number": "UTR99182", "credit_amount": Decimal("130280.00")},
        {"narration": "OTHER DEPOSIT", "reference_number": "UTR11111", "credit_amount": Decimal("5000.00")}
    ]
    result = BankStatementService.match_settlement_to_bank(
        settlement_id="SETTLE-AMZ-NOV-A",
        settlement_deposit_amount=Decimal("130280.00"),
        bank_transactions=bank_txns
    )
    assert result["matched"] is True
    assert result["match_type"] == "exact_reference_and_amount"
    assert result["difference"] == "0.00"

def test_statutory_tax_withholdings():
    # 1.5 Lakh gross sales
    tax_summary = TaxReconciliationService.compute_statutory_taxes(Decimal("150000.00"), period_month="2026-11")
    assert tax_summary["tds_section_194o"]["expected_deduction"] == "1500.00" # 1% of 150000
    assert tax_summary["gst_tcs_section_52"]["expected_deduction"] == "1500.00" # 1% of 150000
    assert tax_summary["total_statutory_withholdings"] == "3000.00"
