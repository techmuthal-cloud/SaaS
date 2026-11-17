import pytest
from decimal import Decimal
from app.services.reconciliation_engine import ReconciliationEngine
from app.models.entities import OrderRecord, SettlementTransaction

def test_deterministic_exact_match():
    orders = [
        OrderRecord(
            external_order_id="402-1234567-0000001",
            sku="SKU-CHAIR-01",
            net_order_amount=Decimal("1200.00")
        )
    ]
    settlements = [
        SettlementTransaction(
            external_order_id="402-1234567-0000001",
            transaction_type="Order",
            amount=Decimal("1200.00")
        )
    ]
    
    result = ReconciliationEngine.reconcile("ws-1", "run-1", orders, settlements)
    summary = result["summary"]
    
    assert summary["matched_count"] == 1
    assert summary["discrepancy_count"] == 0
    assert summary["partial_count"] == 0

def test_fee_overcharge_discrepancy():
    orders = [
        OrderRecord(
            external_order_id="402-1234567-0000002",
            sku="SKU-TABLE-01",
            net_order_amount=Decimal("1500.00")
        )
    ]
    settlements = [
        # Marketplace only paid 1150 (unexpected 350 deduction)
        SettlementTransaction(
            external_order_id="402-1234567-0000002",
            transaction_type="Order",
            amount=Decimal("1150.00")
        )
    ]
    
    result = ReconciliationEngine.reconcile("ws-1", "run-1", orders, settlements)
    summary = result["summary"]
    discrepancies = result["discrepancies"]
    
    assert summary["partial_count"] == 1
    assert len(discrepancies) == 1
    assert discrepancies[0].category == "fee_overcharge"
    assert discrepancies[0].difference_amount == Decimal("-350.00")
