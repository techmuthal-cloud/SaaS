import logging
import hashlib
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Strict allowlists: Zero financial numbers, order IDs, SKUs, or customer PII can ever pass through
ALLOWED_EVENTS = {
    "workspace_created",
    "import_started",
    "import_completed",
    "reconciliation_started",
    "reconciliation_completed",
    "dispute_manifest_exported",
    "tally_exported"
}

ALLOWED_PROPERTIES = {
    "environment",
    "status",
    "marketplace",
    "rows_count",
    "discrepancy_count",
    "duration_seconds"
}

class TelemetryService:
    """
    Privacy-First Product Telemetry via PostHog.
    Uses strict allowlists for event names and properties.
    Pseudonymizes all workspace/user identifiers using one-way SHA-256 hashes.
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
        if event_name not in ALLOWED_EVENTS:
            logger.debug(f"Telemetry rejected unapproved event name: {event_name}")
            return

        # Pseudonymize distinct_id with truncated SHA-256 hash
        pseudonymous_id = hashlib.sha256(str(distinct_id).encode("utf-8")).hexdigest()[:16]

        sanitized_props: Dict[str, Any] = {
            "environment": settings.ENVIRONMENT
        }

        if properties:
            for k, v in properties.items():
                if k in ALLOWED_PROPERTIES:
                    if isinstance(v, (str, int, float, bool)):
                        sanitized_props[k] = v

        client = cls.get_client()
        if client:
            try:
                client.capture(distinct_id=pseudonymous_id, event=event_name, properties=sanitized_props)
            except Exception as e:
                logger.debug(f"Telemetry capture error: {e}")
        else:
            logger.debug(f"[Telemetry Mock] {pseudonymous_id} -> {event_name}: {sanitized_props}")
