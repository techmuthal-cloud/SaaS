from decimal import Decimal
from typing import List, Dict, Any

class MultiMarketplacePivotService:
    """
    Standardizes differing marketplace fee labels into one universal format.
    Allows stacking Amazon India, Flipkart, and Meesho side-by-side in a single stacked pivot table.
    """

    UNIVERSAL_CATEGORIES = [
        "Gross Order Sales",
        "Referral / Commission Fee",
        "Fixed Closing Fee",
        "Fulfillment & Shipping Fee",
        "Customer Returns Debited",
        "Account Reserve Held",
        "Previous Reserve Released",
        "Ad Spend Deductions",
        "Net Settlement Payout"
    ]

    @classmethod
    def generate_stacked_pivot(cls, all_settlement_txns: List[Any], all_stores: List[Any]) -> Dict[str, Any]:
        store_map = {s.id: s for s in all_stores}

        # Initialize breakdown by marketplace
        pivot_data: Dict[str, Dict[str, Decimal]] = {
            "amazon_in": {cat: Decimal("0.0") for cat in cls.UNIVERSAL_CATEGORIES},
            "flipkart": {cat: Decimal("0.0") for cat in cls.UNIVERSAL_CATEGORIES},
            "meesho": {cat: Decimal("0.0") for cat in cls.UNIVERSAL_CATEGORIES},
        }

        for t in all_settlement_txns:
            amt = t.amount or Decimal("0.0")
            ttype = (t.transaction_type or "").lower()
            store = store_map.get(t.store_id)
            mkt = store.marketplace_code if store else "amazon_in"
            if mkt not in pivot_data:
                mkt = "amazon_in"

            if "order" in ttype and amt > 0:
                pivot_data[mkt]["Gross Order Sales"] += amt
            elif "commission" in ttype or "referral" in ttype:
                pivot_data[mkt]["Referral / Commission Fee"] += abs(amt)
            elif "closing" in ttype or "fixed" in ttype:
                pivot_data[mkt]["Fixed Closing Fee"] += abs(amt)
            elif "shipping" in ttype or "pick" in ttype or "fba" in ttype:
                pivot_data[mkt]["Fulfillment & Shipping Fee"] += abs(amt)
            elif "refund" in ttype or "return" in ttype:
                pivot_data[mkt]["Customer Returns Debited"] += abs(amt)
            elif "previous_reserve" in ttype:
                pivot_data[mkt]["Previous Reserve Released"] += abs(amt)
            elif "reserve" in ttype:
                pivot_data[mkt]["Account Reserve Held"] += abs(amt)
            elif "ad" in ttype or "promo" in ttype:
                pivot_data[mkt]["Ad Spend Deductions"] += abs(amt)

        # Calculate Net Payout for each
        for mkt in pivot_data:
            gross = pivot_data[mkt]["Gross Order Sales"]
            ref = pivot_data[mkt]["Referral / Commission Fee"]
            close = pivot_data[mkt]["Fixed Closing Fee"]
            ful = pivot_data[mkt]["Fulfillment & Shipping Fee"]
            ret = pivot_data[mkt]["Customer Returns Debited"]
            res_held = pivot_data[mkt]["Account Reserve Held"]
            res_rel = pivot_data[mkt]["Previous Reserve Released"]
            ads = pivot_data[mkt]["Ad Spend Deductions"]

            net = gross - ref - close - ful - ret - res_held + res_rel - ads
            pivot_data[mkt]["Net Settlement Payout"] = net

        # Format into clean matrix rows for frontend table
        rows = []
        for cat in cls.UNIVERSAL_CATEGORIES:
            az_val = pivot_data["amazon_in"][cat]
            fk_val = pivot_data["flipkart"][cat]
            ms_val = pivot_data["meesho"][cat]
            total_val = az_val + fk_val + ms_val

            rows.append({
                "universal_fee_category": cat,
                "amazon_in": float(az_val),
                "flipkart": float(fk_val),
                "meesho": float(ms_val),
                "total_stacked": float(total_val),
                "is_net": cat == "Net Settlement Payout"
            })

        return {
            "categories": cls.UNIVERSAL_CATEGORIES,
            "rows": rows
        }
