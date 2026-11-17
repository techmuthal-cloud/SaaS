from decimal import Decimal
from typing import List, Dict, Any
from datetime import datetime, timedelta

class CohortReturnLinkingService:
    """
    Cohort-Based Return Tracking:
    Attributes customer returns back to the ORIGINAL ORDER DATE & SKU rather than the settlement date.
    Protects current-period margins and flags products with delayed return leakage.
    """

    @classmethod
    def analyze_cohort_returns(cls, order_records: List[Any], settlement_txns: List[Any]) -> Dict[str, Any]:
        order_map = {o.external_order_id: o for o in order_records}
        sku_cohorts: Dict[str, Dict[str, Any]] = {}

        now = datetime.utcnow()

        # Step 1: Collect Orders by SKU
        for o in order_records:
            sku = o.sku or "UNKNOWN_SKU"
            if sku not in sku_cohorts:
                sku_cohorts[sku] = {
                    "sku": sku,
                    "units_sold": 0,
                    "gross_revenue": Decimal("0.0"),
                    "returns_count": 0,
                    "refunded_amount": Decimal("0.0"),
                    "lag_days_list": []
                }
            sku_cohorts[sku]["units_sold"] += 1
            sku_cohorts[sku]["gross_revenue"] += (o.net_order_amount or Decimal("0.0"))

        # Step 2: Attribute refunds back to the original order's SKU
        for t in settlement_txns:
            amt = t.amount or Decimal("0.0")
            ttype = (t.transaction_type or "").lower()
            if "refund" in ttype or (amt < 0 and "commission" not in ttype and "shipping" not in ttype):
                order_id = t.external_order_id
                matched_order = order_map.get(order_id)
                if matched_order:
                    sku = matched_order.sku or "UNKNOWN_SKU"
                    if sku in sku_cohorts:
                        sku_cohorts[sku]["returns_count"] += 1
                        sku_cohorts[sku]["refunded_amount"] += abs(amt)
                        
                        # Calculate time lag between order date and refund settlement
                        ord_date = matched_order.created_at or (now - timedelta(days=25))
                        ref_date = t.transaction_date or t.created_at or now
                        lag = abs((ref_date - ord_date).days) if isinstance(ref_date, datetime) and isinstance(ord_date, datetime) else 18
                        sku_cohorts[sku]["lag_days_list"].append(lag)

        cohort_results = []
        for sku, data in sku_cohorts.items():
            units = data["units_sold"]
            ret_count = data["returns_count"]
            rate = (ret_count / units * 100) if units > 0 else 0.0
            avg_lag = (sum(data["lag_days_list"]) / len(data["lag_days_list"])) if data["lag_days_list"] else 0
            net_earned = data["gross_revenue"] - data["refunded_amount"]

            cohort_results.append({
                "sku": sku,
                "units_dispatched": units,
                "gross_dispatched_revenue": float(data["gross_revenue"]),
                "returns_count": ret_count,
                "refunded_loss": float(data["refunded_amount"]),
                "realized_return_rate_pct": round(rate, 1),
                "avg_return_lag_days": round(avg_lag, 0),
                "net_cohort_revenue": float(net_earned),
                "is_high_return_risk": rate > 15.0
            })

        return {
            "cohort_summary": cohort_results
        }
