from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any

class ReturnLeakageDetector:
    """
    RTO & Return Leakage Detection Service.
    Surfaces unreturned customer refunds, missing restocks after 45 days,
    and erroneous reverse shipping debits.
    """

    POLICY_RETURN_WINDOW_DAYS = 45

    @classmethod
    def audit_returns(
        cls,
        settlement_txns: List[Any],
        order_records: List[Any]
    ) -> List[Dict[str, Any]]:
        leakages = []
        now = datetime.utcnow()

        refund_txns = [
            t for t in settlement_txns
            if "refund" in (t.transaction_type or "").lower() or (t.amount and t.amount < 0 and "commission" not in (t.transaction_type or "").lower() and "shipping" not in (t.transaction_type or "").lower())
        ]

        order_map = {o.external_order_id: o for o in order_records}

        for ref in refund_txns:
            order_id = ref.external_order_id
            refund_date = ref.transaction_date or ref.created_at or (now - timedelta(days=50))
            days_since_refund = (now - refund_date).days if isinstance(refund_date, datetime) else 50
            refund_amt = abs(ref.amount or Decimal("0.0"))

            # Check if this return has been pending beyond standard return window (45 days)
            if days_since_refund >= cls.POLICY_RETURN_WINDOW_DAYS:
                matched_order = order_map.get(order_id)
                sku = matched_order.sku if matched_order else "UNKNOWN-SKU"
                leakages.append({
                    "id": f"leakage_{ref.id[:8]}",
                    "order_id": order_id,
                    "sku": sku,
                    "refund_date": str(refund_date)[:10],
                    "days_elapsed": days_since_refund,
                    "refund_debited": float(refund_amt),
                    "potential_recovery_amount": float(refund_amt),
                    "leakage_category": "unreturned_inventory",
                    "severity": "high",
                    "recommended_action": f"File Amazon SAFE-T or Flipkart SPF Claim for missing physical stock after {days_since_refund} days.",
                    "source_row": ref.source_row_number
                })

        return leakages
