from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import date

class RateCardEngine:
    """
    Versioned Rate Card Engine for Indian Marketplaces.
    Computes deterministic expected fees (Referral Fee, Closing Fee, Weight Handling)
    based on product category, selling price band, and weight slab.
    """
    VERSION = "2026-v1"

    # Default baseline rate card rules (Category -> {referral_pct, closing_fee, weight_fee})
    AMAZON_RATES = {
        "Furniture": {
            "referral_pct": Decimal("0.125"), # 12.5%
            "closing_fee": Decimal("25.00"),
            "weight_fee": Decimal("65.00")
        },
        "Electronics": {
            "referral_pct": Decimal("0.080"), # 8.0%
            "closing_fee": Decimal("20.00"),
            "weight_fee": Decimal("55.00")
        },
        "Apparel": {
            "referral_pct": Decimal("0.130"), # 13.0%
            "closing_fee": Decimal("20.00"),
            "weight_fee": Decimal("50.00")
        },
        "Default": {
            "referral_pct": Decimal("0.100"), # 10.0%
            "closing_fee": Decimal("20.00"),
            "weight_fee": Decimal("60.00")
        }
    }

    FLIPKART_RATES = {
        "Furniture": {
            "referral_pct": Decimal("0.135"), # 13.5%
            "closing_fee": Decimal("20.00"),
            "pick_pack_fee": Decimal("35.00"),
            "weight_fee": Decimal("65.00")
        },
        "Default": {
            "referral_pct": Decimal("0.100"),
            "closing_fee": Decimal("15.00"),
            "pick_pack_fee": Decimal("25.00"),
            "weight_fee": Decimal("55.00")
        }
    }

    MEESHO_RATES = {
        # Meesho operates primarily on zero-commission model for suppliers
        "Default": {
            "referral_pct": Decimal("0.000"), # 0% commission
            "closing_fee": Decimal("0.00"),
            "shipping_fee": Decimal("65.00") # flat logistics
        }
    }

    @classmethod
    def calculate_expected_fees(
        cls,
        marketplace_code: str,
        gross_price: Decimal,
        category: str = "Default",
        weight_grams: int = 500
    ) -> Dict[str, Decimal]:
        """
        Calculates expected fees deterministically using exact Decimal arithmetic.
        """
        mkt = marketplace_code.lower()
        if "amazon" in mkt:
            rule = cls.AMAZON_RATES.get(category, cls.AMAZON_RATES["Default"])
            referral = (gross_price * rule["referral_pct"]).quantize(Decimal("0.01"))
            closing = rule["closing_fee"]
            shipping = rule["weight_fee"]
            total_fees = referral + closing + shipping
            expected_net = gross_price - total_fees
            return {
                "referral_fee": referral,
                "closing_fee": closing,
                "shipping_fee": shipping,
                "total_fees": total_fees,
                "expected_net_payout": expected_net
            }
        elif "flipkart" in mkt:
            rule = cls.FLIPKART_RATES.get(category, cls.FLIPKART_RATES["Default"])
            referral = (gross_price * rule["referral_pct"]).quantize(Decimal("0.01"))
            closing = rule["closing_fee"]
            pick_pack = rule.get("pick_pack_fee", Decimal("25.00"))
            shipping = rule["weight_fee"]
            total_fees = referral + closing + pick_pack + shipping
            expected_net = gross_price - total_fees
            return {
                "commission": referral,
                "closing_fee": closing,
                "pick_pack_fee": pick_pack,
                "shipping_fee": shipping,
                "total_fees": total_fees,
                "expected_net_payout": expected_net
            }
        else: # Meesho
            rule = cls.MEESHO_RATES.get(category, cls.MEESHO_RATES["Default"])
            shipping = rule["shipping_fee"]
            total_fees = shipping
            expected_net = gross_price - total_fees
            return {
                "commission": Decimal("0.00"),
                "shipping_fee": shipping,
                "total_fees": total_fees,
                "expected_net_payout": expected_net
            }
