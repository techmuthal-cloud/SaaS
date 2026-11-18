import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import ImportRecord, SourceRecord, SettlementTransaction

logger = logging.getLogger(__name__)

class JobQueueService:
    """
    Durable Background Processing & Idempotent Execution Pipeline.
    Manages asynchronous file imports and reconciliation jobs.
    """
    @staticmethod
    def create_import_job(
        workspace_id: str,
        import_id: str,
        db: Session
    ) -> str:
        job_id = str(uuid.uuid4())
        import_rec = db.query(ImportRecord).filter(
            ImportRecord.id == import_id,
            ImportRecord.workspace_id == workspace_id
        ).first()

        if import_rec:
            import_rec.job_id = job_id
            import_rec.status = "processing"
            db.commit()

        return job_id

    @staticmethod
    def check_duplicate_upload(
        workspace_id: str,
        sha256_hash: str,
        db: Session
    ) -> Optional[ImportRecord]:
        """
        Idempotency check: Detects if exact file was already imported and completed.
        """
        existing = db.query(ImportRecord).filter(
            ImportRecord.workspace_id == workspace_id,
            ImportRecord.sha256 == sha256_hash,
            ImportRecord.status == "completed"
        ).first()
        return existing

    @staticmethod
    def purge_failed_import_artifacts(
        workspace_id: str,
        import_id: str,
        db: Session
    ):
        """
        Ensures idempotent retry: safely removes any partial records from a previous failed run.
        """
        try:
            db.query(SourceRecord).filter(
                SourceRecord.workspace_id == workspace_id,
                SourceRecord.import_id == import_id
            ).delete()
            db.query(SettlementTransaction).filter(
                SettlementTransaction.workspace_id == workspace_id,
                SettlementTransaction.import_id == import_id
            ).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to purge partial records for import {import_id}: {e}")

    @staticmethod
    def mark_job_completed(
        workspace_id: str,
        import_id: str,
        row_count: int,
        accepted_count: int,
        rejected_count: int,
        db: Session
    ):
        import_rec = db.query(ImportRecord).filter(
            ImportRecord.id == import_id,
            ImportRecord.workspace_id == workspace_id
        ).first()
        if import_rec:
            import_rec.status = "completed"
            import_rec.row_count = row_count
            import_rec.accepted_count = accepted_count
            import_rec.rejected_count = rejected_count
            import_rec.processed_at = datetime.utcnow()
            db.commit()

    @staticmethod
    def mark_job_failed(
        workspace_id: str,
        import_id: str,
        error_summary: Dict[str, Any],
        db: Session
    ):
        import_rec = db.query(ImportRecord).filter(
            ImportRecord.id == import_id,
            ImportRecord.workspace_id == workspace_id
        ).first()
        if import_rec:
            import_rec.status = "failed"
            import_rec.error_summary = error_summary
            import_rec.processed_at = datetime.utcnow()
            db.commit()
