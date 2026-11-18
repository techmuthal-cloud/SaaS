import html
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Hardened Transactional Email Delivery via Resend.
    - Strictly escapes dynamic variables to prevent HTML/XSS injection.
    - Never logs raw invitation tokens or URLs.
    - Fails safely in production environments if RESEND_API_KEY is not configured.
    """
    @staticmethod
    def send_workspace_invitation(to_email: str, workspace_name: str, invite_link: str) -> bool:
        if not settings.RESEND_API_KEY:
            if settings.ENVIRONMENT in ("production", "staging"):
                logger.error("Email delivery failed: RESEND_API_KEY is not configured in production!")
                return False
            logger.info(f"[Email Mock] Workspace invitation queued for recipient: {to_email}")
            return True

        safe_ws_name = html.escape(workspace_name)
        safe_invite_link = html.escape(invite_link)

        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": f"Invitation to join {safe_ws_name} on SellerFlow AI",
                "html": f"""
                <div style="font-family: sans-serif; padding: 24px; color: #1e293b;">
                    <h2>Workspace Invitation</h2>
                    <p>You have been invited to collaborate on the <strong>{safe_ws_name}</strong> workspace.</p>
                    <p style="margin: 24px 0;">
                        <a href="{safe_invite_link}" style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Accept Invitation</a>
                    </p>
                    <p style="color: #64748b; font-size: 13px;">This invitation link will expire in 48 hours.</p>
                </div>
                """
            })
            return True
        except Exception as e:
            logger.error(f"Resend invitation email dispatch failed: {e}")
            return False

    @staticmethod
    def send_reconciliation_alert(to_email: str, workspace_name: str, settlement_id: str, discrepancy_count: int) -> bool:
        if not settings.RESEND_API_KEY:
            if settings.ENVIRONMENT in ("production", "staging"):
                logger.error("Email delivery failed: RESEND_API_KEY is not configured in production!")
                return False
            logger.info(f"[Email Mock] Recon alert queued for recipient: {to_email}")
            return True

        safe_ws_name = html.escape(workspace_name)
        safe_settlement_id = html.escape(settlement_id)

        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": f"Reconciliation Alert: {discrepancy_count} Discrepancies Flagged",
                "html": f"""
                <div style="font-family: sans-serif; padding: 24px; color: #1e293b;">
                    <h2>Reconciliation Completed</h2>
                    <p>Settlement <strong>{safe_settlement_id}</strong> in <strong>{safe_ws_name}</strong> has been audited.</p>
                    <p>Audit result: {discrepancy_count} discrepancies identified for review.</p>
                </div>
                """
            })
            return True
        except Exception as e:
            logger.error(f"Resend reconciliation alert dispatch failed: {e}")
            return False
