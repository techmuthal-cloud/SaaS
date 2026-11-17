import csv
import io
import re
from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime, date

class BankStatementService:
    """
    Parses bank statements (HDFC, ICICI, SBI, Generic CSV)
    Normalizes bank deposits (credits) and matches them to Marketplace Settlement disbursements.
    """

    CANONICAL_COLUMNS = {
        "date": "value_date",
        "value_date": "value_date",
        "transaction_date": "value_date",
        "txn_date": "value_date",
        "narration": "narration",
        "description": "narration",
        "particulars": "narration",
        "transaction_details": "narration",
        "ref_no": "reference_number",
        "chq_ref_no": "reference_number",
        "reference_number": "reference_number",
        "utr": "reference_number",
        "debit": "debit_amount",
        "withdrawal": "debit_amount",
        "credit": "credit_amount",
        "deposit": "credit_amount",
        "balance": "balance",
        "closing_balance": "balance"
    }

    @classmethod
    def clean_header(cls, header: str) -> str:
        cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', str(header).strip().lower())
        return re.sub(r'[\s_\-]+', '_', cleaned)

    @classmethod
    def parse_csv(cls, stream: io.StringIO) -> List[Dict[str, Any]]:
        reader = csv.reader(stream)
        headers = []
        parsed_txns = []

        for row_idx, row in enumerate(reader, start=1):
            if not row or not any(field.strip() for field in row):
                continue
            if not headers:
                # Find header row
                candidate = [cls.clean_header(h) for h in row]
                if any(c in candidate for c in ("credit", "deposit", "narration", "description", "value_date", "date")):
                    headers = candidate
                    continue
                else:
                    continue

            row_dict = {}
            for col_idx, cell in enumerate(row):
                if col_idx < len(headers):
                    mapped = cls.CANONICAL_COLUMNS.get(headers[col_idx])
                    if mapped:
                        row_dict[mapped] = cell.strip()

            if "credit_amount" in row_dict or "debit_amount" in row_dict:
                # Normalize amounts
                credit = Decimal("0.00")
                if row_dict.get("credit_amount"):
                    c_clean = re.sub(r'[^\d.-]', '', row_dict["credit_amount"])
                    if c_clean:
                        credit = Decimal(c_clean)

                debit = Decimal("0.00")
                if row_dict.get("debit_amount"):
                    d_clean = re.sub(r'[^\d.-]', '', row_dict["debit_amount"])
                    if d_clean:
                        debit = Decimal(d_clean)

                parsed_txns.append({
                    "source_row": row_idx,
                    "value_date": row_dict.get("value_date", datetime.utcnow().strftime("%Y-%m-%d")),
                    "narration": row_dict.get("narration", "Bank Transaction"),
                    "reference_number": row_dict.get("reference_number"),
                    "credit_amount": credit,
                    "debit_amount": debit,
                    "raw_payload": row_dict
                })

        return parsed_txns

    @classmethod
    def match_settlement_to_bank(
        cls,
        settlement_id: str,
        settlement_deposit_amount: Decimal,
        bank_transactions: List[Dict[str, Any]],
        tolerance_inr: Decimal = Decimal("1.00")
    ) -> Dict[str, Any]:
        """
        Reconciles marketplace settlement disbursement to real bank credits.
        Matches by settlement ID in bank narration or exact credit amount.
        """
        best_match = None
        variance = settlement_deposit_amount

        for txn in bank_transactions:
            credit = txn.get("credit_amount", Decimal("0.00"))
            narration = txn.get("narration", "").upper()

            # Check reference / narration match
            has_ref = settlement_id.upper() in narration or (txn.get("reference_number") and settlement_id.upper() in txn.get("reference_number").upper())
            amount_diff = abs(credit - settlement_deposit_amount)

            if has_ref and amount_diff <= tolerance_inr:
                return {
                    "settlement_id": settlement_id,
                    "matched": True,
                    "match_type": "exact_reference_and_amount",
                    "bank_credit": str(credit),
                    "settlement_amount": str(settlement_deposit_amount),
                    "difference": str(amount_diff),
                    "bank_txn": txn
                }
            elif amount_diff <= tolerance_inr and best_match is None:
                best_match = {
                    "settlement_id": settlement_id,
                    "matched": True,
                    "match_type": "exact_amount_match",
                    "bank_credit": str(credit),
                    "settlement_amount": str(settlement_deposit_amount),
                    "difference": str(amount_diff),
                    "bank_txn": txn
                }

        if best_match:
            return best_match

        return {
            "settlement_id": settlement_id,
            "matched": False,
            "match_type": "unmatched_bank_credit",
            "bank_credit": "0.00",
            "settlement_amount": str(settlement_deposit_amount),
            "difference": str(settlement_deposit_amount),
            "bank_txn": None
        }
