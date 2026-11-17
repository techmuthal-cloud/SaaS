from decimal import Decimal
from typing import Dict, Any, Optional

class DisputeGeneratorService:
    """
    Automated Dispute Package Generator.
    Produces copy-pasteable claims with exact marketplace references, policy citations,
    and attached tabular calculation proofs.
    """

    @classmethod
    def generate_dispute_package(
        cls,
        discrepancy: Dict[str, Any],
        marketplace: str = "amazon_in",
        seller_company: str = "Seller Partner"
    ) -> Dict[str, Any]:
        order_id = discrepancy.get("external_order_id") or "UNKNOWN_ORDER"
        category = discrepancy.get("category", "fee_overcharge")
        diff_amount = abs(Decimal(str(discrepancy.get("difference_amount", "0.0"))))
        source_row = discrepancy.get("source_row_number")

        subject = ""
        body = ""
        action_step = ""

        if category in ("fee_overcharge", "variance"):
            subject = f"Incorrect Fee Deduction & Dimensional Overcharge Claim - Order ID: {order_id}"
            body = (
                f"Dear Seller Support Team,\n\n"
                f"We are requesting an immediate reimbursement review for fee overcharges deducted on Order #{order_id}.\n\n"
                f"DISCREPANCY SUMMARY:\n"
                f"-----------------------------------------\n"
                f"- Order ID: {order_id}\n"
                f"- Marketplace: {marketplace.upper()}\n"
                f"- Disputed Amount: INR ₹{diff_amount:.2f}\n"
                f"- Settlement Audit Reference: Source Statement Row #{source_row or 'N/A'}\n\n"
                f"REASON FOR DISPUTE:\n"
                f"The weight handling / commission fee debited on this settlement statement exceeds the agreed "
                f"rate-card slab for this category and volumetric tier. Our registered dimensions and item package weight "
                f"classify this item at the lower slab.\n\n"
                f"REQUESTED RESOLUTION:\n"
                f"1. Please re-verify the package cubing / weight scan for this order.\n"
                f"2. Initiate a manual reimbursement of INR ₹{diff_amount:.2f} to our disbursement ledger.\n\n"
                f"Thank you,\n"
                f"{seller_company}"
            )
            action_step = "Paste into Amazon Seller Central > Help > Get Support > 'Fee calculation issue' or Flipkart Ticket Center."

        elif category in ("unmatched_order", "missing_payout"):
            subject = f"Unsettled Order Disbursement Claim - Order ID: {order_id}"
            body = (
                f"Dear Seller Support Team,\n\n"
                f"According to our dispatched order records, Order #{order_id} was successfully delivered to the customer, "
                f"but has not been remitted in our settlement disbursement cycle.\n\n"
                f"DETAILS:\n"
                f"- Order ID: {order_id}\n"
                f"- Expected Net Settlement: INR ₹{diff_amount:.2f}\n"
                f"- Status: Missing Payout in Settlement Statement\n\n"
                f"Please verify proof of delivery and release the pending settlement balance of INR ₹{diff_amount:.2f} "
                f"in our next upcoming disbursement cycle.\n\n"
                f"Regards,\n"
                f"{seller_company}"
            )
            action_step = "Submit under Payments & Disbursements > Missing Remittance."

        elif "return" in category or "rto" in category:
            subject = f"SAFE-T / Inventory Reimbursement Claim: Customer Return Not Received - Order ID: {order_id}"
            body = (
                f"Dear Seller Support Team,\n\n"
                f"A customer refund was debited against our account for Order #{order_id}, however physical inventory "
                f"has NOT been returned to our warehouse within the 45-day policy grace period.\n\n"
                f"DETAILS:\n"
                f"- Order ID: {order_id}\n"
                f"- Debited Refund Value: INR ₹{diff_amount:.2f}\n"
                f"- Physical Restock: NOT RECEIVED / RTO MISSING\n\n"
                f"In accordance with marketplace lost-in-transit policy, please issue an immediate reimbursement credit "
                f"for the cost of lost merchandise.\n\n"
                f"Regards,\n"
                f"{seller_company}"
            )
            action_step = "File under Amazon SAFE-T Claim or Flipkart Protection Fund (SPF)."

        else:
            subject = f"Settlement Variance Inquiry - Order ID: {order_id}"
            body = (
                f"Dear Support,\n\n"
                f"Please review an unexplained settlement variance of INR ₹{diff_amount:.2f} on Order #{order_id}."
            )
            action_step = "Submit inquiry via Seller Portal."

        csv_proof = (
            f"Field,Value\n"
            f"Order_ID,{order_id}\n"
            f"Marketplace,{marketplace}\n"
            f"Discrepancy_INR,{diff_amount:.2f}\n"
            f"Source_Row_Number,{source_row or ''}\n"
            f"Audit_Status,VERIFIED_UNEXPLAINED_VARIANCE\n"
        )

        return {
            "order_id": order_id,
            "dispute_subject": subject,
            "dispute_body": body,
            "action_step": action_step,
            "disputed_amount": float(diff_amount),
            "csv_proof": csv_proof
        }
