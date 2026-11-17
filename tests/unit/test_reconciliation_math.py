import pytest
from decimal import Decimal
from app.services.reconciliation_engine import ReconciliationEngine
from app.services.rate_card_engine import RateCardEngine
from app.models.entities import OrderRecord, SettlementTransaction

def test_rate_card_deterministic_fee_calculation():
    """Verify rate card engine computes exact decimal fees without floats."""
    calc = RateCardEngine.calculate_expected_fees("amazon_in", Decimal("1500.00"), category="Furniture")
    # Furniture referral: 12.5% of 1500 = 187.50, Closing: 25.00, Weight: 65.00 -> Total fees: 277.50
    assert calc["referral_fee"] == Decimal("187.50")
    assert calc["closing_fee"] == Decimal("25.00")
    assert calc["shipping_fee"] == Decimal("65.00")
    assert calc["total_fees"] == Decimal("277.50")
    assert calc["expected_net_payout"] == Decimal("1222.50")

def test_normal_marketplace_fees_do_not_flag_false_overcharge():
    """
    CRITICAL FINANCIAL INVARIANT:
    When Amazon deducts normal contracted fees, the order must be MATCHED,
    NOT classified as a fee overcharge!
    """
    orders = [
        OrderRecord(
            external_order_id="402-1000001-0000001",
            sku="SKU-CHAIR-01",
            gross_amount=Decimal("1500.00"),
            net_order_amount=Decimal("1500.00")
        )
    ]
    # Amazon settlement lines: ItemPrice = 1500, Commission = -187.50, Closing = -25.00, Shipping = -65.00
    # Net actual payout = 1222.50
    settlements = [
        SettlementTransaction(external_order_id="402-1000001-0000001", transaction_type="Order", amount_type="ItemPrice", amount=Decimal("1500.00")),
        SettlementTransaction(external_order_id="402-1000001-0000001", transaction_type="Commission", amount=Decimal("-187.50")),
        SettlementTransaction(external_order_id="402-1000001-0000001", transaction_type="ClosingFee", amount=Decimal("-25.00")),
        SettlementTransaction(external_order_id="402-1000001-0000001", transaction_type="ShippingCharge", amount=Decimal("-65.00")),
    ]

    result = ReconciliationEngine.reconcile("ws-1", "run-1", orders, settlements, marketplace_code="amazon_in")
    summary = result["summary"]
    discrepancies = result["discrepancies"]

    assert summary["matched_count"] == 1
    assert summary["partial_count"] == 0
    assert summary["discrepancy_count"] == 0
    assert summary["recoverable_amount"] == "0.00"
    assert len(discrepancies) == 0

def test_true_fee_overcharge_detected_with_exact_math():
    """When marketplace deducts an unexpected extra 150 INR, flag fee_overcharge."""
    orders = [
        OrderRecord(
            external_order_id="402-1000002-0000002",
            sku="SKU-CHAIR-01",
            gross_amount=Decimal("1500.00"),
            net_order_amount=Decimal("1500.00")
        )
    ]
    # Marketplace paid only 1072.50 instead of 1222.50 (an unexplained 150 INR overcharge)
    settlements = [
        SettlementTransaction(external_order_id="402-1000002-0000002", transaction_type="Order", amount=Decimal("1072.50"))
    ]

    result = ReconciliationEngine.reconcile("ws-1", "run-1", orders, settlements, marketplace_code="amazon_in")
    summary = result["summary"]
    discrepancies = result["discrepancies"]

    assert summary["partial_count"] == 1
    assert summary["discrepancy_count"] == 1
    assert summary["recoverable_amount"] == "150.00"
    assert discrepancies[0].category == "fee_overcharge"
    assert discrepancies[0].difference_amount == Decimal("-150.00")

def test_rounding_tolerance_within_one_rupee():
    """Tolerate small fractional penny differences within 1 INR."""
    orders = [
        OrderRecord(
            external_order_id="402-1000003-0000003",
            sku="SKU-CHAIR-01",
            gross_amount=Decimal("1500.00")
        )
    ]
    # Actual payout is 1222.80 (30 paise difference from expected 1222.50)
    settlements = [
        SettlementTransaction(external_order_id="402-1000003-0000003", transaction_type="Order", amount=Decimal("1222.80"))
    ]

    result = ReconciliationEngine.reconcile("ws-1", "run-1", orders, settlements, marketplace_code="amazon_in")
    assert result["summary"]["matched_count"] == 1
    assert result["summary"]["discrepancy_count"] == 0

def test_missing_payout_detection():
    """When an order exists in catalog but zero payout is in settlement, flag missing_payout."""
    orders = [
        OrderRecord(
            external_order_id="402-MISSING-001",
            sku="SKU-LAMP-01",
            gross_amount=Decimal("800.00")
        )
    ]
    settlements = []

    result = ReconciliationEngine.reconcile("ws-1", "run-1", orders, settlements, marketplace_code="amazon_in")
    assert result["summary"]["unmatched_count"] == 1
    assert result["summary"]["discrepancy_count"] == 1
    assert result["discrepancies"][0].category == "missing_payout"

def test_unmatched_settlement_record():
    """When a payout arrives with an unknown order ID, flag unmatched_order without corrupting ledger."""
    orders = []
    settlements = [
        SettlementTransaction(external_order_id="402-UNKNOWN-999", transaction_type="Order", amount=Decimal("750.00"))
    ]

    result = ReconciliationEngine.reconcile("ws-1", "run-1", orders, settlements, marketplace_code="amazon_in")
    assert result["summary"]["unmatched_count"] == 1
    assert result["summary"]["discrepancy_count"] == 1
    assert result["discrepancies"][0].category == "unmatched_order"
