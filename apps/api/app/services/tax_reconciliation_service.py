from decimal import Decimal
from typing import List, Dict, Any
from app.models.entities import SettlementTransaction

class TaxReconciliationService:
    """
    Computes and segregates Indian statutory tax withholdings:
    - Section 194-O TDS (Income Tax - 1% on Gross GMV)
    - Section 52 GST TCS (1% - 0.5% CGST + 0.5% SGST or 1% IGST)
    Keeps tax reporting distinct from commercial fee deductions.
    """

    TDS_194O_RATE = Decimal("0.0100") # 1.0%
    GST_TCS_RATE = Decimal("0.0100")  # 1.0%

    @classmethod
    def compute_statutory_taxes(
        cls,
        gross_sales: Decimal,
        period_month: str = "2026-11"
    ) -> Dict[str, Any]:
        tds_expected = (gross_sales * cls.TDS_194O_RATE).quantize(Decimal("0.01"))
        tcs_expected = (gross_sales * cls.GST_TCS_RATE).quantize(Decimal("0.01"))

        return {
            "period_month": period_month,
            "gross_taxable_sales": str(gross_sales.quantize(Decimal("0.01"))),
            "tds_section_194o": {
                "section": "194-O (Income Tax)",
                "rate": "1.00%",
                "expected_deduction": str(tds_expected)
            },
            "gst_tcs_section_52": {
                "section": "Section 52 (CGST/SGST/IGST)",
                "rate": "1.00%",
                "expected_deduction": str(tcs_expected)
            },
            "total_statutory_withholdings": str((tds_expected + tcs_expected).quantize(Decimal("0.01")))
        }
