from decimal import Decimal
from typing import List, Dict, Any
from app.models.entities import SettlementTransaction, OrderRecord, ReconciliationMatch, Discrepancy

class ReconciliationEngine:
    """
    Deterministic rule-based matching engine.
    Calculates expected settlements against actual marketplace payouts.
    Flags fee overcharges, missing payouts, and discrepancies.
    """
    RULESET_VERSION = "v1.0.0-deterministic"

    @classmethod
    def reconcile(
        cls,
        workspace_id: str,
        run_id: str,
        orders: List[OrderRecord],
        settlements: List[SettlementTransaction]
    ) -> Dict[str, Any]:
        order_map: Dict[str, List[OrderRecord]] = {}
        for o in orders:
            order_map.setdefault(o.external_order_id, []).append(o)

        settlement_map: Dict[str, List[SettlementTransaction]] = {}
        unlinked_settlements: List[SettlementTransaction] = []
        for s in settlements:
            if s.external_order_id:
                settlement_map.setdefault(s.external_order_id, []).append(s)
            else:
                unlinked_settlements.append(s)

        matches: List[ReconciliationMatch] = []
        discrepancies: List[Discrepancy] = []

        total_expected = Decimal("0.0")
        total_actual = Decimal("0.0")
        total_difference = Decimal("0.0")

        all_order_ids = set(order_map.keys()).union(set(settlement_map.keys()))

        for order_id in all_order_ids:
            ords = order_map.get(order_id, [])
            txns = settlement_map.get(order_id, [])

            exp_amt = sum((o.net_order_amount or Decimal("0.0")) for o in ords)
            act_amt = sum((t.amount or Decimal("0.0")) for t in txns)
            diff = act_amt - exp_amt

            total_expected += exp_amt
            total_actual += act_amt
            total_difference += abs(diff)

            # Determine Match Status
            if not ords and txns:
                status = "unmatched"
                matches.append(ReconciliationMatch(
                    workspace_id=workspace_id,
                    run_id=run_id,
                    match_group_key=order_id,
                    match_status=status,
                    expected_amount=Decimal("0.0"),
                    actual_amount=act_amt,
                    difference_amount=act_amt,
                    matching_rule="missing_order_record",
                    evidence={"tx_count": len(txns), "types": [t.transaction_type for t in txns]}
                ))
                discrepancies.append(Discrepancy(
                    workspace_id=workspace_id,
                    run_id=run_id,
                    category="unmatched_order",
                    severity="medium",
                    title=f"Unmatched Settlement for Order {order_id}",
                    explanation=f"Settlement of ₹{act_amt} exists in marketplace report, but no order record was found.",
                    external_order_id=order_id,
                    difference_amount=act_amt,
                    source_row_number=txns[0].source_row_number if txns else None
                ))
            elif ords and not txns:
                status = "unmatched"
                matches.append(ReconciliationMatch(
                    workspace_id=workspace_id,
                    run_id=run_id,
                    match_group_key=order_id,
                    match_status=status,
                    expected_amount=exp_amt,
                    actual_amount=Decimal("0.0"),
                    difference_amount=-exp_amt,
                    matching_rule="missing_settlement",
                    evidence={"sku": ords[0].sku if ords else None}
                ))
                discrepancies.append(Discrepancy(
                    workspace_id=workspace_id,
                    run_id=run_id,
                    category="missing_payout",
                    severity="high",
                    title=f"Missing Payout for Order {order_id}",
                    explanation=f"Expected payout of ₹{exp_amt} is missing from the settlement statement.",
                    external_order_id=order_id,
                    difference_amount=-exp_amt
                ))
            else:
                # Both Order and Settlement exist
                # If difference is within 1 rupee rounding tolerance
                if abs(diff) <= Decimal("1.00"):
                    status = "matched"
                else:
                    status = "partial"
                    # Flag fee overcharge or unexpected deduction
                    discrepancies.append(Discrepancy(
                        workspace_id=workspace_id,
                        run_id=run_id,
                        category="fee_overcharge" if diff < 0 else "variance",
                        severity="high" if abs(diff) > Decimal("100.00") else "medium",
                        title=f"Settlement Discrepancy for Order {order_id}",
                        explanation=f"Expected ₹{exp_amt}, received ₹{act_amt} (Difference: ₹{diff}). Check fee breakdown.",
                        external_order_id=order_id,
                        difference_amount=diff,
                        source_row_number=txns[0].source_row_number if txns else None
                    ))

                matches.append(ReconciliationMatch(
                    workspace_id=workspace_id,
                    run_id=run_id,
                    match_group_key=order_id,
                    match_status=status,
                    expected_amount=exp_amt,
                    actual_amount=act_amt,
                    difference_amount=diff,
                    matching_rule="exact_order_id",
                    evidence={"order_count": len(ords), "txn_count": len(txns)}
                ))

        summary = {
            "ruleset_version": cls.RULESET_VERSION,
            "total_orders": len(all_order_ids),
            "matched_count": sum(1 for m in matches if m.match_status == "matched"),
            "partial_count": sum(1 for m in matches if m.match_status == "partial"),
            "unmatched_count": sum(1 for m in matches if m.match_status == "unmatched"),
            "discrepancy_count": len(discrepancies),
            "total_expected": str(total_expected),
            "total_actual": str(total_actual),
            "total_difference": str(total_difference)
        }

        return {
            "summary": summary,
            "matches": matches,
            "discrepancies": discrepancies
        }
