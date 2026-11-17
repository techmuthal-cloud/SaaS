import os
import io
import pytest
from decimal import Decimal
from app.services.amazon_adapter import AmazonSettlementAdapter
from app.services.multimarketplace_adapters import FlipkartSettlementAdapter, MeeshoSettlementAdapter

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))

def test_amazon_settlement_fixture_parsing():
    fixture_path = os.path.join(FIXTURES_DIR, "sample_amazon_settlement.tsv")
    with open(fixture_path, "r", encoding="utf-8") as f:
        stream = io.StringIO(f.read())

    raw_rows = AmazonSettlementAdapter.parse_csv_stream(stream)
    assert len(raw_rows) > 0

    norm_rows = [AmazonSettlementAdapter.normalize_row(r) for r in raw_rows]
    for nr in norm_rows:
        assert nr["order_id"] is not None
        assert nr["currency"] == "INR"
        assert isinstance(nr["amount"], Decimal)
        assert nr["amount"] != Decimal("0.00")

def test_flipkart_settlement_with_underscore_headers():
    """Verify that Flipkart headers with underscores parse non-zero amounts correctly."""
    fixture_path = os.path.join(FIXTURES_DIR, "sample_flipkart_settlement.csv")
    with open(fixture_path, "r", encoding="utf-8") as f:
        stream = io.StringIO(f.read())

    raw_rows = FlipkartSettlementAdapter.parse_csv_stream(stream)
    assert len(raw_rows) > 0

    norm_rows = [FlipkartSettlementAdapter.normalize_row(r) for r in raw_rows]
    # Check first row (OD40291029102: settlement_value = 1380.00)
    first = norm_rows[0]
    assert first["order_id"] == "OD40291029102"
    assert first["amount"] == Decimal("1380.00"), f"Expected 1380.00 but got {first['amount']}"
    assert first["posted_date"] == "2026-11-02"

def test_meesho_settlement_with_underscore_headers():
    """Verify that Meesho headers with underscores (final_settlement_amount) parse non-zero amounts."""
    fixture_path = os.path.join(FIXTURES_DIR, "sample_meesho_settlement.csv")
    with open(fixture_path, "r", encoding="utf-8") as f:
        stream = io.StringIO(f.read())

    raw_rows = MeeshoSettlementAdapter.parse_csv_stream(stream)
    assert len(raw_rows) > 0

    norm_rows = [MeeshoSettlementAdapter.normalize_row(r) for r in raw_rows]
    # Check first row (MEESH-902910: final_settlement_amount = 420.00)
    first = norm_rows[0]
    assert first["order_id"] == "MEESH-902910"
    assert first["amount"] == Decimal("420.00"), f"Expected 420.00 but got {first['amount']}"
    assert first["posted_date"] == "2026-11-01"
