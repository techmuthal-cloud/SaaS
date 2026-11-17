import csv
import io
import re
from decimal import Decimal
from typing import Dict, Any, List
import openpyxl

class FlipkartSettlementAdapter:
    """
    Parser for Flipkart Payment & Settlement Reports.
    Handles Flipkart commission slabs, pick & pack fees, reverse shipping, and fixed closing fees.
    """
    MARKETPLACE_CODE = "flipkart"

    CANONICAL_FIELD_MAPPING = {
        "order_id": "order_id",
        "order_item_id": "order_item_id",
        "fsn": "sku",
        "sku": "sku",
        "seller_sku": "sku",
        "transaction_type": "transaction_type",
        "type": "transaction_type",
        "order_type": "transaction_type",
        "settlement_value": "amount",
        "net_amount": "amount",
        "bank_settlement_value": "amount",
        "total_offer_price": "gross_amount",
        "commission": "commission",
        "marketplace_fee": "commission",
        "fixed_fee": "fixed_fee",
        "collection_fee": "collection_fee",
        "pick_and_pack_fee": "pick_pack_fee",
        "pick_pack_fee": "pick_pack_fee",
        "shipping_fee": "shipping_fee",
        "reverse_shipping_fee": "reverse_shipping_fee",
        "order_date": "order_date",
        "settlement_date": "posted_date",
        "payment_date": "posted_date",
    }

    @classmethod
    def clean_header(cls, header: str) -> str:
        cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', str(header).strip().lower())
        return re.sub(r'[\s_\-]+', '_', cleaned)

    @classmethod
    def parse_csv_stream(cls, stream: io.StringIO) -> List[Dict[str, Any]]:
        sample = stream.read(4096)
        stream.seek(0)
        delimiter = '\t' if '\t' in sample and sample.count('\t') > sample.count(',') else ','
        reader = csv.reader(stream, delimiter=delimiter)
        headers = []
        rows = []
        for row_idx, row in enumerate(reader, start=1):
            if not row or not any(field.strip() for field in row):
                continue
            if not headers:
                headers = [cls.clean_header(h) for h in row]
                continue
            row_dict = {}
            for col_idx, cell_value in enumerate(row):
                if col_idx < len(headers):
                    row_dict[headers[col_idx]] = cell_value.strip()
            row_dict["_source_row"] = row_idx
            rows.append(row_dict)
        return rows

    @classmethod
    def parse_xlsx_bytes(cls, content: bytes) -> List[Dict[str, Any]]:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        sheet = wb.active
        rows = []
        headers = []
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if not row or not any(row):
                continue
            if not headers:
                headers = [cls.clean_header(c) if c is not None else f"col_{i}" for i, c in enumerate(row)]
                continue
            row_dict = {}
            for col_idx, val in enumerate(row):
                if col_idx < len(headers):
                    row_dict[headers[col_idx]] = str(val).strip() if val is not None else ""
            row_dict["_source_row"] = row_idx
            rows.append(row_dict)
        return rows

    @classmethod
    def normalize_row(cls, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            "source_row": raw_row.get("_source_row"),
            "order_id": None,
            "sku": None,
            "transaction_type": "Order",
            "amount": Decimal("0.00"),
            "currency": "INR",
            "posted_date": None,
            "fees_breakdown": {},
            "raw_payload": raw_row
        }

        for raw_col, val in raw_row.items():
            mapped_key = cls.CANONICAL_FIELD_MAPPING.get(raw_col)
            if mapped_key == "order_id" and val:
                normalized["order_id"] = val
            elif mapped_key == "sku" and val:
                normalized["sku"] = val
            elif mapped_key == "transaction_type" and val:
                normalized["transaction_type"] = val
            elif mapped_key == "posted_date" and val:
                normalized["posted_date"] = val
            elif mapped_key == "amount" and val:
                try:
                    clean_amt = re.sub(r'[^\d.-]', '', val)
                    if clean_amt:
                        normalized["amount"] = Decimal(clean_amt)
                except Exception:
                    normalized["amount"] = Decimal("0.00")
            elif mapped_key in ("commission", "pick_pack_fee", "shipping_fee", "fixed_fee", "reverse_shipping_fee") and val:
                try:
                    clean_amt = re.sub(r'[^\d.-]', '', val)
                    if clean_amt:
                        normalized["fees_breakdown"][mapped_key] = Decimal(clean_amt)
                except Exception:
                    pass

        return normalized


class MeeshoSettlementAdapter:
    """
    Parser for Meesho Payment & Deductions Reports.
    Handles zero-commission marketplace model, return shipping charges, COD deductions, and supplier payouts.
    """
    MARKETPLACE_CODE = "meesho"

    CANONICAL_FIELD_MAPPING = {
        "sub_order_no": "order_id",
        "sub_order_number": "order_id",
        "order_id": "order_id",
        "product_name": "sku",
        "sku": "sku",
        "supplier_sku": "sku",
        "return_type": "return_type",
        "payment_date": "posted_date",
        "settlement_date": "posted_date",
        "final_settlement_amount": "amount",
        "net_settlement_amount": "amount",
        "bank_transfer_amount": "amount",
        "settlement_amount": "amount",
        "total_sale_amount": "gross_amount",
        "shipping_charge": "shipping_fee",
        "return_shipping_charge": "return_shipping_fee",
        "rto_charge": "rto_charge",
        "penalty": "penalty",
        "waiver": "waiver"
    }

    @classmethod
    def clean_header(cls, header: str) -> str:
        cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', str(header).strip().lower())
        return re.sub(r'[\s_\-]+', '_', cleaned)

    @classmethod
    def parse_csv_stream(cls, stream: io.StringIO) -> List[Dict[str, Any]]:
        sample = stream.read(4096)
        stream.seek(0)
        delimiter = '\t' if '\t' in sample and sample.count('\t') > sample.count(',') else ','
        reader = csv.reader(stream, delimiter=delimiter)
        headers = []
        rows = []
        for row_idx, row in enumerate(reader, start=1):
            if not row or not any(field.strip() for field in row):
                continue
            if not headers:
                headers = [cls.clean_header(h) for h in row]
                continue
            row_dict = {}
            for col_idx, cell_value in enumerate(row):
                if col_idx < len(headers):
                    row_dict[headers[col_idx]] = cell_value.strip()
            row_dict["_source_row"] = row_idx
            rows.append(row_dict)
        return rows

    @classmethod
    def parse_xlsx_bytes(cls, content: bytes) -> List[Dict[str, Any]]:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        sheet = wb.active
        rows = []
        headers = []
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if not row or not any(row):
                continue
            if not headers:
                headers = [cls.clean_header(c) if c is not None else f"col_{i}" for i, c in enumerate(row)]
                continue
            row_dict = {}
            for col_idx, val in enumerate(row):
                if col_idx < len(headers):
                    row_dict[headers[col_idx]] = str(val).strip() if val is not None else ""
            row_dict["_source_row"] = row_idx
            rows.append(row_dict)
        return rows

    @classmethod
    def normalize_row(cls, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            "source_row": raw_row.get("_source_row"),
            "order_id": None,
            "sku": None,
            "transaction_type": "Order",
            "amount": Decimal("0.00"),
            "currency": "INR",
            "posted_date": None,
            "fees_breakdown": {},
            "raw_payload": raw_row
        }

        for raw_col, val in raw_row.items():
            mapped_key = cls.CANONICAL_FIELD_MAPPING.get(raw_col)
            if mapped_key == "order_id" and val:
                normalized["order_id"] = val
            elif mapped_key == "sku" and val:
                normalized["sku"] = val
            elif mapped_key == "posted_date" and val:
                normalized["posted_date"] = val
            elif mapped_key == "amount" and val:
                try:
                    clean_amt = re.sub(r'[^\d.-]', '', val)
                    if clean_amt:
                        normalized["amount"] = Decimal(clean_amt)
                except Exception:
                    normalized["amount"] = Decimal("0.00")
            elif mapped_key in ("shipping_fee", "return_shipping_fee", "rto_charge", "penalty", "waiver") and val:
                try:
                    clean_amt = re.sub(r'[^\d.-]', '', val)
                    if clean_amt:
                        normalized["fees_breakdown"][mapped_key] = Decimal(clean_amt)
                except Exception:
                    pass

        return normalized
