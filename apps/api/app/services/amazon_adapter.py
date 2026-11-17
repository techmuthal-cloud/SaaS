import csv
import io
import re
from decimal import Decimal
from typing import Dict, Any, List, Optional
import openpyxl

class AmazonSettlementAdapter:
    """
    Adapter for parsing and normalizing Amazon India Settlement Reports
    Supports flat-file V2 (.csv/.tsv/.txt) and Excel (.xlsx) formats.
    """
    MARKETPLACE_CODE = "amazon_in"

    CANONICAL_FIELD_MAPPING = {
        "order_id": "order_id",
        "orderid": "order_id",
        "transaction_type": "transaction_type",
        "type": "transaction_type",
        "amount_type": "amount_type",
        "amount_description": "amount_description",
        "amount": "amount",
        "total": "amount",
        "settlement_amount": "amount",
        "posted_date": "posted_date",
        "posted_date_time": "posted_date",
        "date_time": "posted_date",
        "date": "posted_date",
        "sku": "sku",
        "quantity_purchased": "quantity",
        "quantity": "quantity",
        "currency": "currency",
    }

    @classmethod
    def clean_header(cls, header: str) -> str:
        # Standardize spaces, underscores, and hyphens into lowercase snake_case
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
                    col_name = headers[col_idx]
                    row_dict[col_name] = cell_value.strip()
            
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
                    col_name = headers[col_idx]
                    row_dict[col_name] = str(val).strip() if val is not None else ""
            row_dict["_source_row"] = row_idx
            rows.append(row_dict)
        return rows

    @classmethod
    def normalize_row(cls, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            "source_row": raw_row.get("_source_row"),
            "order_id": None,
            "sku": None,
            "transaction_type": "Other",
            "amount_type": None,
            "amount_description": None,
            "amount": Decimal("0.00"),
            "currency": "INR",
            "posted_date": None,
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
            elif mapped_key == "amount_type" and val:
                normalized["amount_type"] = val
            elif mapped_key == "amount_description" and val:
                normalized["amount_description"] = val
            elif mapped_key == "currency" and val:
                normalized["currency"] = val.upper()
            elif mapped_key == "amount" and val:
                try:
                    clean_amt = re.sub(r'[^\d.-]', '', val)
                    if clean_amt:
                        normalized["amount"] = Decimal(clean_amt)
                except Exception:
                    normalized["amount"] = Decimal("0.00")
            elif mapped_key == "posted_date" and val:
                normalized["posted_date"] = val

        return normalized
