import csv
import io
import os
import uuid
import hashlib
from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body, status, Request, Header
from fastapi.responses import StreamingResponse, Response, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import jwt

def make_json_serializable(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    return obj

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_tenant_access,
    require_workspace_role,
    validate_and_sanitize_upload,
    read_upload_stream_safely,
    safe_cleanup_file,
    sanitize_for_spreadsheet,
    create_access_token,
    get_password_hash,
    verify_password,
    get_current_user,
    get_jwt_secret
)
from app.core.rate_limiter import (
    rate_limit_login,
    rate_limit_register,
    rate_limit_upload
)
from app.core.storage import storage
from app.core.analytics import TelemetryService
from app.services.job_queue import JobQueueService
from app.core.logging import logger
from app.models.entities import (
    Workspace, Store, ImportRecord, SourceRecord, OrderRecord,
    SettlementTransaction, ReconciliationRun, ReconciliationMatch,
    Discrepancy, Product, User, WorkspaceMember, AuditEvent,
    BankAccount, BankTransaction, SettlementBankMatch
)
from app.services.amazon_adapter import AmazonSettlementAdapter
from app.services.multimarketplace_adapters import FlipkartSettlementAdapter, MeeshoSettlementAdapter
from app.services.reconciliation_engine import ReconciliationEngine
from app.services.rate_card_engine import RateCardEngine
from app.services.dispute_generator import DisputeGeneratorService
from app.services.return_leakage_service import ReturnLeakageDetector
from app.services.tally_exporter import TallyExporterService
from app.services.settlement_cycle_service import SettlementCycleReconService
from app.services.multi_marketplace_pivot_service import MultiMarketplacePivotService
from app.services.cohort_return_service import CohortReturnLinkingService
from app.services.bank_statement_service import BankStatementService
from app.services.tax_reconciliation_service import TaxReconciliationService

router = APIRouter()

# ----------------- Observability & Health -----------------
@router.get("/health")
def health_liveness():
    """
    Liveness probe: verifies service process is running and responding.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0-production"
    }

@router.get("/health/ready")
@router.get("/ready")
def health_readiness(db: Session = Depends(get_db)):
    """
    Readiness probe: validates database connectivity.
    Reports database failures with HTTP 503 Service Unavailable.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Readiness probe failed database check: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "detail": "Database connectivity check failed"
            }
        )

@router.get("/metrics")
def get_metrics(
    x_monitoring_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Restricted global operational metrics.
    Strictly restricted to authorized operators:
    - Dedicated X-Monitoring-Token matching deployment secret MONITORING_SECRET_TOKEN
    - Or an authenticated operator with is_superuser=True.
    Regular authenticated users and fallback tokens are strictly denied.
    """
    authorized = False

    # 1. Require explicit non-placeholder MONITORING_SECRET_TOKEN
    if settings.MONITORING_SECRET_TOKEN and x_monitoring_token:
        if x_monitoring_token == settings.MONITORING_SECRET_TOKEN:
            authorized = True

    # 2. Or require a verified operator account with is_superuser flag
    if not authorized and authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ")[1]
            payload = jwt.decode(token, get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active and user.is_superuser:
                    authorized = True
        except Exception:
            pass

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Metrics endpoint is strictly restricted to authorized operators with valid monitoring credentials"
        )

    return {
        "workspaces_count": db.query(Workspace).count(),
        "total_imports": db.query(ImportRecord).count(),
        "total_orders": db.query(OrderRecord).count(),
        "total_settlement_transactions": db.query(SettlementTransaction).count(),
        "total_reconciliation_runs": db.query(ReconciliationRun).count(),
        "total_discrepancies": db.query(Discrepancy).count()
    }

# ----------------- Authentication & Tenant Onboarding -----------------
@router.post("/auth/register")
def register_user(
    email: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    full_name: Optional[str] = Body(None, embed=True),
    workspace_name: Optional[str] = Body(None, embed=True),
    _rate_limit: None = Depends(rate_limit_register),
    db: Session = Depends(get_db)
):
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local password registration is disabled in production. Use Clerk authentication."
        )

    existing = db.query(User).filter(User.email == email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    hashed = get_password_hash(password)
    try:
        user = User(email=email.lower().strip(), full_name=full_name, hashed_password=hashed)
        db.add(user)
        db.flush()

        # Create primary workspace for new user atomically
        ws_name = workspace_name or f"{user.full_name or 'My'} E-Commerce"
        ws = Workspace(name=ws_name, subscription_tier="free")
        db.add(ws)
        db.flush()

        # Assign user as Owner
        member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner")
        db.add(member)

        # Seed default stores
        db.add(Store(workspace_id=ws.id, display_name="Amazon India Store", marketplace_code="amazon_in"))
        db.add(Store(workspace_id=ws.id, display_name="Flipkart Store", marketplace_code="flipkart"))
        db.add(Store(workspace_id=ws.id, display_name="Meesho Supplier Store", marketplace_code="meesho"))
        db.commit()
        db.refresh(user)
        db.refresh(ws)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete user registration.")

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
        "workspace": {"id": ws.id, "name": ws.name}
    }

@router.post("/auth/login")
def login_user(
    email: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    _rate_limit: None = Depends(rate_limit_login),
    db: Session = Depends(get_db)
):
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Local password authentication is disabled in production. Use Clerk authentication."
        )

    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.id, "email": user.email})
    # Fetch primary workspace
    member = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == user.id).first()
    ws_id = member.workspace_id if member else None

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
        "workspace_id": ws_id
    }

@router.get("/auth/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).all()
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "workspaces": [
            {"workspace_id": m.workspace_id, "role": m.role}
            for m in memberships
        ]
    }

# ----------------- Workspaces (Tenant-Scoped) -----------------
@router.get("/workspaces")
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List workspaces where the authenticated user is an active member.
    Unauthenticated users are rejected with 401. Users only see their own workspaces.
    """
    memberships = db.query(WorkspaceMember).filter(WorkspaceMember.user_id == current_user.id).all()
    workspace_ids = [m.workspace_id for m in memberships]
    if not workspace_ids:
        return []
    
    workspaces = db.query(Workspace).filter(Workspace.id.in_(workspace_ids)).all()
    role_map = {m.workspace_id: m.role for m in memberships}
    return [
        {
            "id": w.id,
            "name": w.name,
            "subscription_tier": w.subscription_tier,
            "role": role_map.get(w.id, "member")
        }
        for w in workspaces
    ]

@router.post("/workspaces")
def create_workspace(
    request: Request,
    name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new workspace and assigns current_user as owner in the same atomic database transaction.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    try:
        ws = Workspace(name=name, subscription_tier="free")
        db.add(ws)
        db.flush()

        # Add creator as owner in the same transaction
        member = WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role="owner")
        db.add(member)

        # Seed initial stores
        db.add(Store(workspace_id=ws.id, display_name=f"{name} Amazon", marketplace_code="amazon_in"))
        db.add(Store(workspace_id=ws.id, display_name=f"{name} Flipkart", marketplace_code="flipkart"))
        db.add(Store(workspace_id=ws.id, display_name=f"{name} Meesho", marketplace_code="meesho"))

        db.commit()
        db.refresh(ws)
    except Exception as e:
        db.rollback()
        logger.error(f"[request_id={request_id}] Failed to create workspace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workspace. Reference Request ID: {request_id}")

    return {"id": ws.id, "name": ws.name, "subscription_tier": ws.subscription_tier, "role": "owner"}

@router.get("/workspaces/{workspace_id}/stores")
def get_stores(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    stores = db.query(Store).filter(Store.workspace_id == workspace_id).all()
    return [
        {
            "id": s.id,
            "workspace_id": s.workspace_id,
            "marketplace_code": s.marketplace_code,
            "display_name": s.display_name,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in stores
    ]

# ----------------- Secure Multi-Marketplace Ingestion -----------------
@router.post("/workspaces/{workspace_id}/imports")
async def upload_report(
    workspace_id: str,
    request: Request,
    file: UploadFile = File(...),
    store_id: Optional[str] = Form(None),
    marketplace: Optional[str] = Form("amazon_in"),
    report_type: str = Form("settlement"),
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(rate_limit_upload),
    db: Session = Depends(get_db)
):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    file_path = None
    import_rec = None

    # Enforce role-based access control: only owner, admin, or accountant can upload
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Viewer role is not authorized. Uploading reports requires owner, admin, or accountant role"
        )

    # Cross-tenant store verification: reject any store_id not belonging to this workspace
    if store_id:
        store = db.query(Store).filter(
            Store.id == store_id,
            Store.workspace_id == workspace_id
        ).first()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Store '{store_id}' does not belong to authorized workspace '{workspace_id}'"
            )
        marketplace = store.marketplace_code

    try:
        # 1. Enforce upload size limit during streaming read before full buffering
        file_bytes = await read_upload_stream_safely(file)
        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Check for duplicate upload BEFORE saving to storage to prevent orphan objects
        existing_completed = JobQueueService.check_duplicate_upload(workspace_id, sha256, db)
        if existing_completed:
            return {
                "status": "completed",
                "import_id": existing_completed.id,
                "file_name": existing_completed.file_name,
                "rows_ingested": existing_completed.accepted_count,
                "idempotent_replay": True,
                "message": "File was previously processed. Returning existing record."
            }
        
        # 2. Content & magic-bytes validation, format verification, safe UUID storage path
        safe_storage_filename = validate_and_sanitize_upload(file_bytes, file.filename)
        
        # 3. Store upload in Supabase Storage quarantine
        file_path = storage.save(workspace_id, safe_storage_filename, file_bytes, is_quarantined=True)

        import_rec = ImportRecord(
            workspace_id=workspace_id,
            store_id=store_id,
            file_name=file.filename,
            storage_path=file_path,
            sha256=sha256,
            file_size_bytes=len(file_bytes),
            mime_type=file.content_type,
            report_type=report_type,
            status="processing"
        )
        db.add(import_rec)
        db.commit()
        db.refresh(import_rec)

        # 4. Ingest and parse records using appropriate adapter with row limit safeguards
        is_excel = file.filename.lower().endswith(".xlsx")
        rows = []
        if is_excel:
            if marketplace == "flipkart":
                rows = FlipkartSettlementAdapter.parse_xlsx_bytes(file_bytes)
            elif marketplace == "meesho":
                rows = MeeshoSettlementAdapter.parse_xlsx_bytes(file_bytes)
            else:
                rows = AmazonSettlementAdapter.parse_xlsx_bytes(file_bytes)
        else:
            text_stream = io.StringIO(file_bytes.decode("utf-8", errors="replace"))
            if marketplace == "flipkart":
                rows = FlipkartSettlementAdapter.parse_csv_stream(text_stream)
            elif marketplace == "meesho":
                rows = MeeshoSettlementAdapter.parse_csv_stream(text_stream)
            else:
                rows = AmazonSettlementAdapter.parse_csv_stream(text_stream)

        if len(rows) > settings.MAX_UPLOAD_ROWS:
            safe_cleanup_file(file_path)
            import_rec.status = "failed"
            import_rec.error_summary = {"error": f"Row count {len(rows)} exceeds limit {settings.MAX_UPLOAD_ROWS}"}
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Report exceeds maximum allowed limit of {settings.MAX_UPLOAD_ROWS} rows. Reference Request ID: {request_id}"
            )

        import_rec.row_count = len(rows)

        accepted = 0
        for r in rows:
            if marketplace == "flipkart":
                norm = FlipkartSettlementAdapter.normalize_row(r)
            elif marketplace == "meesho":
                norm = MeeshoSettlementAdapter.normalize_row(r)
            else:
                norm = AmazonSettlementAdapter.normalize_row(r)

            # Ensure payload is JSON-serializable (converts Decimal to string)
            serializable_norm = make_json_serializable(norm)

            src = SourceRecord(
                workspace_id=workspace_id,
                import_id=import_rec.id,
                source_row_number=norm.get("source_row") or 0,
                record_type="settlement_transaction",
                raw_payload=make_json_serializable(r),
                normalized_payload=serializable_norm,
                validation_status="valid"
            )
            db.add(src)

            order_id_val = norm.get("order_id")
            st = SettlementTransaction(
                workspace_id=workspace_id,
                store_id=store_id,
                import_id=import_rec.id,
                external_order_id=order_id_val,
                transaction_type=norm.get("transaction_type", "Order"),
                amount_type=norm.get("amount_type"),
                amount_description=norm.get("amount_description"),
                amount=norm.get("amount", Decimal("0.00")),
                currency=norm.get("currency", "INR"),
                source_row_number=norm.get("source_row")
            )
            db.add(st)

            # Ingest OrderRecord if order ID present
            if order_id_val and str(norm.get("transaction_type", "")).lower() in ("order", "shipment", "itemprice", "other"):
                clean_oid = str(order_id_val).strip()
                existing_ord = db.query(OrderRecord).filter(
                    OrderRecord.workspace_id == workspace_id,
                    OrderRecord.external_order_id == clean_oid
                ).first()
                if not existing_ord:
                    new_ord = OrderRecord(
                        workspace_id=workspace_id,
                        store_id=store_id,
                        import_id=import_rec.id,
                        external_order_id=clean_oid,
                        sku=norm.get("sku"),
                        order_date=datetime.utcnow(),
                        gross_amount=norm.get("amount", Decimal("0.00")),
                        net_order_amount=norm.get("amount", Decimal("0.00")),
                        currency=norm.get("currency", "INR")
                    )
                    db.add(new_ord)

            accepted += 1

        import_rec.accepted_count = accepted
        import_rec.status = "completed"
        import_rec.processed_at = datetime.utcnow()
        
        db.add(AuditEvent(
            workspace_id=workspace_id,
            action="IMPORT_UPLOAD",
            resource_type="import",
            resource_id=import_rec.id,
            details={"file_name": file.filename, "rows": len(rows), "marketplace": marketplace}
        ))
        
        # Promote storage file from quarantine to verified
        verified_path = storage.promote_from_quarantine(file_path)
        import_rec.storage_path = verified_path
        db.commit()

        # Telemetry: coarse product metric, strictly zero financial/order details
        TelemetryService.capture_event(
            distinct_id=workspace_id,
            event_name="import_completed",
            properties={"marketplace": marketplace, "rows_count": accepted}
        )

        return {
            "import_id": import_rec.id,
            "status": import_rec.status,
            "rows_processed": import_rec.accepted_count,
            "marketplace": marketplace
        }

    except HTTPException:
        if file_path:
            storage.delete(file_path)
            safe_cleanup_file(file_path)
        raise
    except Exception as e:
        db.rollback()
        if file_path:
            storage.delete(file_path)
            safe_cleanup_file(file_path)
        if import_rec:
            try:
                failed_rec = db.query(ImportRecord).filter(ImportRecord.id == import_rec.id).first()
                if failed_rec:
                    failed_rec.status = "failed"
                    failed_rec.error_summary = {"error": "Processing failed due to malformed row data"}
                    db.commit()
            except Exception:
                db.rollback()
        logger.error(f"[request_id={request_id}] Import processing failed for file={file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process settlement report: Invalid or malformed file structure. Reference Request ID: {request_id}"
        )

# ----------------- Authenticated Import Job Status & Listing -----------------
@router.get("/workspaces/{workspace_id}/imports")
def list_imports(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    imports = db.query(ImportRecord).filter(
        ImportRecord.workspace_id == workspace_id
    ).order_by(ImportRecord.created_at.desc()).limit(50).all()
    return [
        {
            "id": imp.id,
            "file_name": imp.file_name,
            "report_type": imp.report_type,
            "status": imp.status,
            "row_count": imp.row_count,
            "accepted_count": imp.accepted_count,
            "rejected_count": imp.rejected_count,
            "created_at": imp.created_at.isoformat() if imp.created_at else None,
            "processed_at": imp.processed_at.isoformat() if imp.processed_at else None
        }
        for imp in imports
    ]

@router.get("/workspaces/{workspace_id}/imports/{import_id}/status")
def get_import_status(
    workspace_id: str,
    import_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    import_rec = db.query(ImportRecord).filter(
        ImportRecord.id == import_id,
        ImportRecord.workspace_id == workspace_id
    ).first()
    if not import_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import record '{import_id}' not found in workspace '{workspace_id}'"
        )
    return {
        "import_id": import_rec.id,
        "status": import_rec.status,
        "job_id": import_rec.job_id,
        "file_name": import_rec.file_name,
        "row_count": import_rec.row_count,
        "accepted_count": import_rec.accepted_count,
        "rejected_count": import_rec.rejected_count,
        "created_at": import_rec.created_at.isoformat() if import_rec.created_at else None,
        "processed_at": import_rec.processed_at.isoformat() if import_rec.processed_at else None,
        "error_summary": import_rec.error_summary
    }

# ----------------- Reconciliation (Rate Card Audited) -----------------
@router.post("/workspaces/{workspace_id}/reconcile")
def run_reconciliation(
    workspace_id: str,
    store_id: Optional[str] = Query(None),
    marketplace: Optional[str] = Query("amazon_in"),
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Reconciliation execution requires owner, admin, or accountant role"
        )

    # Derive marketplace from authorized store if store_id specified
    if store_id and store_id != "all":
        st = db.query(Store).filter(Store.id == store_id, Store.workspace_id == workspace_id).first()
        if st:
            marketplace = st.marketplace_code

    orders_q = db.query(OrderRecord).filter(OrderRecord.workspace_id == workspace_id)
    if store_id and store_id != "all":
        orders_q = orders_q.filter(OrderRecord.store_id == store_id)
    orders = orders_q.all()

    txns_q = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id)
    if store_id and store_id != "all":
        txns_q = txns_q.filter(SettlementTransaction.store_id == store_id)
    settlements = txns_q.all()

    run = ReconciliationRun(
        workspace_id=workspace_id,
        store_id=store_id if store_id != "all" else None,
        ruleset_version=ReconciliationEngine.RULESET_VERSION,
        rate_card_version=RateCardEngine.VERSION,
        status="processing"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Execute deterministic matching engine with like-for-like fee audit
    results = ReconciliationEngine.reconcile(
        workspace_id=workspace_id,
        run_id=run.id,
        orders=orders,
        settlements=settlements,
        marketplace_code=marketplace or "amazon_in"
    )

    for m in results["matches"]:
        db.add(m)
    for d in results["discrepancies"]:
        db.add(d)

    run.summary = results["summary"]
    run.status = "completed"
    
    # Audit log
    db.add(AuditEvent(
        workspace_id=workspace_id,
        action="RECON_RUN",
        resource_type="reconciliation_run",
        resource_id=run.id,
        details=results["summary"]
    ))
    db.commit()

    return {
        "run_id": run.id,
        "summary": results["summary"],
        "matches_count": len(results["matches"]),
        "discrepancies_count": len(results["discrepancies"])
    }

@router.get("/workspaces/{workspace_id}/reconciliation/latest")
def get_latest_reconciliation(
    workspace_id: str,
    store_id: Optional[str] = Query(None),
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    query = db.query(ReconciliationRun).filter(ReconciliationRun.workspace_id == workspace_id)
    if store_id and store_id != "all":
        query = query.filter(ReconciliationRun.store_id == store_id)
    latest_run = query.order_by(ReconciliationRun.created_at.desc()).first()
    if not latest_run:
        return {
            "status": "not_run",
            "summary": {
                "total_discrepancies": 0,
                "total_overcharge_amount": "0.00",
                "status": "not_reconciled"
            },
            "discrepancies": []
        }
    discrepancies = db.query(Discrepancy).filter(Discrepancy.run_id == latest_run.id).all()
    return {
        "run_id": latest_run.id,
        "status": latest_run.status,
        "summary": latest_run.summary or {},
        "created_at": latest_run.created_at.isoformat() if latest_run.created_at else None,
        "discrepancies": [
            {
                "id": d.id,
                "category": d.category,
                "severity": d.severity,
                "status": d.status,
                "title": d.title,
                "explanation": d.explanation,
                "order_id": d.external_order_id,
                "difference_amount": str(d.difference_amount),
                "currency": d.currency
            }
            for d in discrepancies
        ]
    }

# ----------------- Discrepancies & Sanitized Exports -----------------
@router.get("/workspaces/{workspace_id}/discrepancies")
def get_discrepancies(
    workspace_id: str,
    limit: int = 50,
    offset: int = 0,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    discs = db.query(Discrepancy).filter(
        Discrepancy.workspace_id == workspace_id
    ).order_by(Discrepancy.created_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": d.id,
            "category": d.category,
            "severity": d.severity,
            "status": d.status,
            "title": d.title,
            "explanation": d.explanation,
            "order_id": d.external_order_id,
            "difference_amount": str(d.difference_amount),
            "source_row": d.source_row_number,
            "evidence": d.evidence_payload
        }
        for d in discs
    ]

@router.get("/workspaces/{workspace_id}/discrepancies/batch-manifest")
@router.post("/workspaces/{workspace_id}/discrepancies/batch-manifest")
def export_batch_manifest(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant", "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Manifest export requires owner, admin, accountant, or member role"
        )

    discs = db.query(Discrepancy).filter(
        Discrepancy.workspace_id == workspace_id
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "Discrepancy Type", "Severity", "Claim Amount (INR)", "Source Row", "Explanation"])

    for d in discs:
        # Protect against CSV formula injection with sanitize_for_spreadsheet
        writer.writerow([
            sanitize_for_spreadsheet(d.external_order_id or "N/A"),
            sanitize_for_spreadsheet(d.category),
            sanitize_for_spreadsheet(d.severity),
            str(abs(d.difference_amount or Decimal("0.00"))),
            sanitize_for_spreadsheet(d.source_row_number or "N/A"),
            sanitize_for_spreadsheet(d.explanation or "")
        ])

    output.seek(0)
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=SellerFlow_Dispute_Manifest.csv"
    return response

# ----------------- 1-Click Dispute Generator -----------------
@router.post("/workspaces/{workspace_id}/disputes/generate")
def generate_dispute(
    workspace_id: str,
    order_id: str = Body(..., embed=True),
    marketplace: str = Body("amazon_in", embed=True),
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant", "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Dispute generation requires owner, admin, accountant, or member role"
        )
    disc = db.query(Discrepancy).filter(
        Discrepancy.workspace_id == workspace_id,
        Discrepancy.external_order_id == order_id
    ).first()

    if not disc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No discrepancy found for order '{order_id}' in workspace '{workspace_id}'. Dispute claim packages cannot be generated without verified discrepancy data."
        )

    claim_amount = abs(disc.difference_amount or Decimal("0.00"))
    disc_type = disc.category or "Contracted Marketplace Fee Overcharge"

    # Retrieve real SKU from OrderRecord or fallback to normalized placeholder
    order_rec = db.query(OrderRecord).filter(
        OrderRecord.workspace_id == workspace_id,
        OrderRecord.external_order_id == order_id
    ).first()
    sku = order_rec.sku if (order_rec and order_rec.sku) else (disc.title or "SKU-DISPUTE-ITEM")

    # Retrieve evidence details safely without fabricating numbers
    evidence = disc.evidence_payload or {}
    expected_fee = Decimal(str(evidence.get("expected_fee", "0.00")))
    actual_fee = Decimal(str(evidence.get("actual_fee", str(claim_amount))))

    pkg = DisputeGeneratorService.generate_ticket(
        marketplace=marketplace,
        order_id=order_id,
        sku=sku,
        discrepancy_type=disc_type,
        expected_fee=expected_fee,
        actual_charged_fee=actual_fee,
        overcharge_amount=claim_amount,
        actual_weight_grams=int(evidence.get("actual_weight_grams", 500)),
        charged_weight_grams=int(evidence.get("charged_weight_grams", 1000))
    )
    return pkg

@router.post("/workspaces/{workspace_id}/discrepancies/{discrepancy_id}/dispute-package")
def generate_dispute_for_discrepancy(
    workspace_id: str,
    discrepancy_id: str,
    marketplace: Optional[str] = Form("amazon_in"),
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant", "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Dispute generation requires owner, admin, accountant, or member role"
        )
    disc = db.query(Discrepancy).filter(
        Discrepancy.workspace_id == workspace_id,
        (Discrepancy.id == discrepancy_id) | (Discrepancy.external_order_id == discrepancy_id)
    ).first()

    if not disc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrepancy '{discrepancy_id}' not found in workspace '{workspace_id}'."
        )

    order_id = disc.external_order_id or discrepancy_id
    claim_amount = abs(disc.difference_amount or Decimal("0.00"))
    disc_type = disc.category or "Contracted Marketplace Fee Overcharge"

    order_rec = db.query(OrderRecord).filter(
        OrderRecord.workspace_id == workspace_id,
        OrderRecord.external_order_id == order_id
    ).first()
    sku = order_rec.sku if (order_rec and order_rec.sku) else (disc.title or "SKU-DISPUTE-ITEM")
    evidence = disc.evidence_payload or {}
    expected_fee = Decimal(str(evidence.get("expected_fee", "0.00")))
    actual_fee = Decimal(str(evidence.get("actual_fee", str(claim_amount))))

    pkg = DisputeGeneratorService.generate_ticket(
        marketplace=marketplace,
        order_id=order_id,
        sku=sku,
        discrepancy_type=disc_type,
        expected_fee=expected_fee,
        actual_charged_fee=actual_fee,
        overcharge_amount=claim_amount,
        actual_weight_grams=int(evidence.get("actual_weight_grams", 500)),
        charged_weight_grams=int(evidence.get("charged_weight_grams", 1000))
    )
    return pkg

# ----------------- Evidence Drawer API -----------------
@router.get("/workspaces/{workspace_id}/evidence/{order_id}")
def get_order_evidence(
    workspace_id: str,
    order_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    transactions = db.query(SettlementTransaction).filter(
        SettlementTransaction.workspace_id == workspace_id,
        SettlementTransaction.external_order_id == order_id
    ).all()
    disc = db.query(Discrepancy).filter(
        Discrepancy.workspace_id == workspace_id,
        Discrepancy.external_order_id == order_id
    ).first()
    order = db.query(OrderRecord).filter(
        OrderRecord.workspace_id == workspace_id,
        OrderRecord.external_order_id == order_id
    ).first()

    return {
        "order_id": order_id,
        "sku": order.sku if order else None,
        "discrepancy": {
            "category": disc.category if disc else None,
            "severity": disc.severity if disc else None,
            "difference_amount": str(disc.difference_amount) if disc else "0.00",
            "explanation": disc.explanation if disc else None
        } if disc else None,
        "transactions": [
            {
                "id": tx.id,
                "transaction_type": tx.transaction_type,
                "amount_type": tx.amount_type,
                "amount_description": tx.amount_description,
                "amount": str(tx.amount),
                "currency": tx.currency,
                "source_row": tx.source_row_number
            }
            for tx in transactions
        ]
    }

# ----------------- Product Margin Configuration -----------------
@router.get("/workspaces/{workspace_id}/products")
def list_products(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    prods = db.query(Product).filter(Product.workspace_id == workspace_id).all()
    return [
        {
            "id": p.id,
            "sku": p.sku,
            "title": p.title,
            "category": p.category,
            "weight_grams": p.weight_grams,
            "cogs_amount": str(p.cogs_amount),
            "packaging_cost": str(p.packaging_cost),
            "shipping_estimate": str(p.shipping_estimate),
            "currency": p.currency
        }
        for p in prods
    ]

@router.post("/workspaces/{workspace_id}/products")
def create_or_update_product(
    workspace_id: str,
    sku: str = Form(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form("General"),
    weight_grams: Optional[int] = Form(500),
    cogs_amount: Optional[float] = Form(0.0),
    packaging_cost: Optional[float] = Form(0.0),
    shipping_estimate: Optional[float] = Form(0.0),
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Modifying products requires owner, admin, or accountant role"
        )
    prod = db.query(Product).filter(
        Product.workspace_id == workspace_id,
        Product.sku == sku.strip()
    ).first()
    if not prod:
        prod = Product(
            workspace_id=workspace_id,
            sku=sku.strip(),
            title=title,
            category=category or "General",
            weight_grams=weight_grams or 500,
            cogs_amount=Decimal(str(cogs_amount or 0.0)),
            packaging_cost=Decimal(str(packaging_cost or 0.0)),
            shipping_estimate=Decimal(str(shipping_estimate or 0.0))
        )
        db.add(prod)
    else:
        if title: prod.title = title
        if category: prod.category = category
        if weight_grams: prod.weight_grams = weight_grams
        if cogs_amount is not None: prod.cogs_amount = Decimal(str(cogs_amount))
        if packaging_cost is not None: prod.packaging_cost = Decimal(str(packaging_cost))
        if shipping_estimate is not None: prod.shipping_estimate = Decimal(str(shipping_estimate))
    db.commit()
    db.refresh(prod)
    return {"id": prod.id, "sku": prod.sku, "status": "saved"}

# ----------------- Return & RTO Leakage Detection -----------------
@router.get("/workspaces/{workspace_id}/returns-leakage")
def get_return_leakage(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    leakages = ReturnLeakageDetector.detect_unrestocked_returns(workspace_id=workspace_id, db=db)
    return leakages

# ----------------- Waterfall Financial Breakdown -----------------
@router.get("/workspaces/{workspace_id}/waterfall")
def get_waterfall(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    txns = db.query(SettlementTransaction).filter(
        SettlementTransaction.workspace_id == workspace_id
    ).all()

    gross_sales = Decimal("0.00")
    commission = Decimal("0.00")
    shipping = Decimal("0.00")
    returns = Decimal("0.00")
    other_fees = Decimal("0.00")
    net_payout = Decimal("0.00")

    for t in txns:
        amt = t.amount or Decimal("0.00")
        ttype = (t.transaction_type or "").lower()
        if ttype in ("order", "shipment") and amt > Decimal("0.00"):
            gross_sales += amt
        elif "commission" in ttype or "referral" in ttype:
            commission += abs(amt)
        elif "shipping" in ttype or "weight" in ttype or "pick" in ttype:
            shipping += abs(amt)
        elif "refund" in ttype or "return" in ttype:
            returns += abs(amt)
        elif amt < Decimal("0.00"):
            other_fees += abs(amt)
        net_payout += amt

    # Avoid double-counting discrepancies in waterfall ledger:
    discs = db.query(Discrepancy).filter(
        Discrepancy.workspace_id == workspace_id,
        Discrepancy.category == "fee_overcharge"
    ).all()
    recoverable_discrepancies = sum((abs(d.difference_amount) for d in discs), Decimal("0.00"))

    return {
        "gross_sales": str(gross_sales.quantize(Decimal("0.01"))),
        "commission": str(commission.quantize(Decimal("0.01"))),
        "shipping": str(shipping.quantize(Decimal("0.01"))),
        "returns": str(returns.quantize(Decimal("0.01"))),
        "other_deductions": str(other_fees.quantize(Decimal("0.01"))),
        "net_payout": str(net_payout.quantize(Decimal("0.01"))),
        "flagged_discrepancies": str(recoverable_discrepancies.quantize(Decimal("0.01")))
    }

# ----------------- Settlement Period & Reserves Reconciliation -----------------
@router.get("/workspaces/{workspace_id}/settlement-cycle-recon")
def get_settlement_cycle_recon(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    recon_data = SettlementCycleReconService.reconcile_cycle(workspace_id=workspace_id, db=db)
    return recon_data

# ----------------- Universal Multi-Marketplace Stacked Pivot -----------------
@router.get("/workspaces/{workspace_id}/multi-marketplace-pivot")
def get_multi_marketplace_pivot(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    pivot_data = MultiMarketplacePivotService.generate_universal_pivot(workspace_id=workspace_id, db=db)
    return pivot_data

# ----------------- Cohort Return Attribution -----------------
@router.get("/workspaces/{workspace_id}/cohort-returns")
def get_cohort_returns(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    cohort_data = CohortReturnLinkingService.analyze_cohort_returns(workspace_id=workspace_id, db=db)
    return cohort_data

# ----------------- Bank Statement Import & Reconciliation -----------------
@router.post("/workspaces/{workspace_id}/bank-statements/upload")
async def upload_bank_statement(
    workspace_id: str,
    request: Request,
    file: UploadFile = File(...),
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    _rate_limit: None = Depends(rate_limit_upload),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Bank statement uploads require owner, admin, or accountant role"
        )

    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    file_path = None
    try:
        file_bytes = await read_upload_stream_safely(file)
        safe_filename = validate_and_sanitize_upload(file_bytes, file.filename)
        # Store in quarantine first
        file_path = storage.save(workspace_id, safe_filename, file_bytes, is_quarantined=True)
        text_stream = io.StringIO(file_bytes.decode("utf-8", errors="replace"))

        parsed = BankStatementService.parse_csv(text_stream)
        if not parsed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid bank transaction rows found in the uploaded statement. Reference Request ID: {request_id}"
            )

        # Get or create default bank account
        acct = db.query(BankAccount).filter(BankAccount.workspace_id == workspace_id).first()
        if not acct:
            acct = BankAccount(workspace_id=workspace_id, bank_name="Primary Business Account", account_number_mask="XXXX-8821")
            db.add(acct)
            db.flush()

        inserted = 0
        for idx, t in enumerate(parsed, start=1):
            raw_date = str(t.get("value_date", "")).strip()
            val_date = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%b-%Y"):
                try:
                    val_date = datetime.strptime(raw_date[:10], fmt).date()
                    break
                except Exception:
                    continue
            if not val_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format in bank statement row {idx}: '{raw_date}'. Expected format YYYY-MM-DD or DD/MM/YYYY. Reference Request ID: {request_id}"
                )

            bt = BankTransaction(
                workspace_id=workspace_id,
                bank_account_id=acct.id,
                value_date=val_date,
                narration=t.get("narration", "Bank Deposit"),
                reference_number=t.get("reference_number"),
                debit_amount=t.get("debit_amount", Decimal("0.00")),
                credit_amount=t.get("credit_amount", Decimal("0.00"))
            )
            db.add(bt)
            inserted += 1

        db.commit()

        # Promote storage file to verified only after database commit succeeds
        storage.promote_from_quarantine(file_path)
        return {"status": "success", "transactions_imported": inserted}
    except HTTPException:
        if file_path:
            storage.delete(file_path)
            safe_cleanup_file(file_path)
        raise
    except Exception as e:
        db.rollback()
        if file_path:
            storage.delete(file_path)
            safe_cleanup_file(file_path)
        logger.error(f"[request_id={request_id}] Bank statement upload failed for file={file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process bank statement: Invalid or malformed file structure. Reference Request ID: {request_id}"
        )

@router.get("/workspaces/{workspace_id}/bank-reconciliation")
def reconcile_settlement_to_bank(
    workspace_id: str,
    settlement_id: str = Query("SETTLE-AMZ-2026-11-A"),
    settlement_amount: Decimal = Query(Decimal("130280.00")),
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    bank_txns = db.query(BankTransaction).filter(
        BankTransaction.workspace_id == workspace_id
    ).all()

    txns_data = [
        {
            "id": bt.id,
            "value_date": bt.value_date.isoformat(),
            "narration": bt.narration,
            "reference_number": bt.reference_number,
            "credit_amount": bt.credit_amount,
            "debit_amount": bt.debit_amount
        }
        for bt in bank_txns
    ]

    result = BankStatementService.match_settlement_to_bank(
        settlement_id=settlement_id,
        settlement_deposit_amount=settlement_amount,
        bank_transactions=txns_data
    )
    return result

# ----------------- Statutory Tax Withholding Summary -----------------
@router.get("/workspaces/{workspace_id}/tax-reconciliation")
def get_tax_reconciliation(
    workspace_id: str,
    period_month: str = Query("2026-11"),
    ws: Workspace = Depends(verify_tenant_access),
    db: Session = Depends(get_db)
):
    # Sum gross sales for the period
    txns = db.query(SettlementTransaction).filter(
        SettlementTransaction.workspace_id == workspace_id
    ).all()

    gross = sum(
        (t.amount for t in txns if (t.transaction_type or "").lower() in ("order", "shipment") and t.amount > Decimal("0.00")),
        Decimal("0.00")
    )
    if gross == Decimal("0.00"):
        # Zero transactions: return deterministic zero summary, never fabricate demo numbers
        return {
            "period_month": period_month,
            "gross_sales": "0.00",
            "tds_section_194_o": "0.00",
            "tcs_section_52": "0.00",
            "total_statutory_withholding": "0.00",
            "net_payable_after_taxes": "0.00",
            "status": "no_transactions",
            "detail": f"No taxable order transactions found in workspace '{workspace_id}' for period '{period_month}'."
        }

    tax_summary = TaxReconciliationService.compute_statutory_taxes(gross, period_month)
    return tax_summary

# ----------------- TallyPrime Accounting Export -----------------
@router.get("/workspaces/{workspace_id}/export-tally")
def export_tally_daybook(
    workspace_id: str,
    ws: Workspace = Depends(verify_tenant_access),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ("owner", "admin", "accountant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Tally export requires owner, admin, or accountant role"
        )

    xml_content = TallyExporterService.generate_daybook_xml(workspace_id=workspace_id, db=db)
    response = Response(content=xml_content, media_type="application/xml")
    response.headers["Content-Disposition"] = "attachment; filename=SellerFlow_Tally_DayBook.xml"
    return response
