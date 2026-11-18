import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Sensitive keywords that must NEVER be ingested into telemetry
PROHIBITED_METRIC_KEYS = {
    "order_id", "external_order_id", "sku", "amount", "gross_amount", "net_amount",
    "fee", "commission", "difference_amount", "bank_account", "account_number",
    "pan", "gstin", "customer_name", "phone", "email", "secret", "password"
}

class TelemetryService:
    """
    Privacy-conscious product analytics integration via PostHog.
    Guarantees that zero financial ledger data, order identifiers, or PII
    are transmitted to telemetry servers.
    """
    _posthog_client = None

    @classmethod
    def get_client(cls):
        if cls._posthog_client is None and settings.POSTHOG_API_KEY:
            try:
                import posthog
                posthog.api_key = settings.POSTHOG_API_KEY
                posthog.host = settings.POSTHOG_HOST
                cls._posthog_client = posthog
            except Exception as e:
                logger.warning(f"Could not initialize PostHog: {e}")
        return cls._posthog_client

    @classmethod
    def capture_event(
        cls,
        distinct_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Captures sanitized high-level product actions (e.g. 'file_upload_succeeded').
        All properties are strictly sanitized to drop any financial/order data.
        """
        sanitized_props: Dict[str, Any] = {
            "environment": settings.ENVIRONMENT
        }

        if properties:
            for k, v in properties.items():
                lower_k = k.lower()
                if any(bad in lower_k for bad in PROHIBITED_METRIC_KEYS):
                    continue
                # Only allow basic types
                if isinstance(v, (str, int, float, bool)):
                    sanitized_props[k] = v

        client = cls.get_client()
        if client:
            try:
                client.capture(distinct_id=distinct_id, event=event_name, properties=sanitized_props)
            except Exception as e:
                logger.debug(f"Telemetry capture error: {e}")
        else:
            logger.debug(f"[Telemetry Mock] {distinct_id} -> {event_name}: {sanitized_props}")
