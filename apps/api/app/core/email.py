import logging
from typing import Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Transactional email delivery via Resend.
    Strictly restricted to non-sensitive notifications:
    - Workspace invitations
    - Job completion alerts
    Never includes bank account numbers, tax IDs, or itemized financial transaction rows in email bodies.
    """
    @staticmethod
    def send_workspace_invitation(to_email: str, workspace_name: str, invite_link: str) -> bool:
        if not settings.RESEND_API_KEY:
            logger.info(f"[Email Mock] Workspace invitation to {to_email} for {workspace_name}: {invite_link}")
            return True

        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": f"You've been invited to join {workspace_name} on SellerFlow AI",
                "html": f"""
                <div style="font-family: sans-serif; padding: 20px;">
                    <h2>Welcome to SellerFlow AI</h2>
                    <p>You have been invited to collaborate on the <strong>{workspace_name}</strong> workspace.</p>
                    <p><a href="{invite_link}" style="background-color: #4f46e5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">SellerFlow AI — Automated Financial Reconciliation</p>
                </div>
                """
            })
            return True
        except Exception as e:
            logger.error(f"Failed to send invitation email via Resend: {e}")
            return False

    @staticmethod
    def send_reconciliation_alert(to_email: str, workspace_name: str, settlement_id: str, discrepancy_count: int) -> bool:
        if not settings.RESEND_API_KEY:
            logger.info(f"[Email Mock] Recon alert to {to_email} for settlement {settlement_id}: {discrepancy_count} discrepancies found.")
            return True

        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": f"Reconciliation Complete: {discrepancy_count} Discrepancies Detected",
                "html": f"""
                <div style="font-family: sans-serif; padding: 20px;">
                    <h2>Reconciliation Cycle Complete</h2>
                    <p>Settlement <strong>{settlement_id}</strong> in workspace <strong>{workspace_name}</strong> has finished processing.</p>
                    <p>Summary: {discrepancy_count} discrepancies flagged for review.</p>
                    <p>Log in to your SellerFlow dashboard to review and export dispute packages.</p>
                </div>
                """
            })
            return True
        except Exception as e:
            logger.error(f"Failed to send recon alert email via Resend: {e}")
            return False
