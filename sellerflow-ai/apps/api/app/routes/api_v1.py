import csv
import io
import os
import hashlib
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import (
    Workspace, Store, ImportRecord, SourceRecord, OrderRecord,
    SettlementTransaction, ReconciliationRun, ReconciliationMatch,
    Discrepancy, Product
)
from app.services.amazon_adapter import AmazonSettlementAdapter
from app.services.multimarketplace_adapters import FlipkartSettlementAdapter, MeeshoSettlementAdapter
from app.services.reconciliation_engine import ReconciliationEngine
from app.services.dispute_generator import DisputeGeneratorService
from app.services.return_leakage_service import ReturnLeakageDetector
from app.services.tally_exporter import TallyExporterService
from app.services.settlement_cycle_service import SettlementCycleReconService
from app.services.multi_marketplace_pivot_service import MultiMarketplacePivotService
from app.services.cohort_return_service import CohortReturnLinkingService

router = APIRouter()

# ----------------- Workspaces & Multi-Store Management -----------------
@router.get("/workspaces")
def list_workspaces(db: Session = Depends(get_db)):
    workspaces = db.query(Workspace).all()
    if not workspaces:
        ws = Workspace(name="My E-Commerce Business", subscription_tier="free")
        db.add(ws)
        db.commit()
        db.refresh(ws)
        db.add(Store(workspace_id=ws.id, display_name="Amazon India Store", marketplace_code="amazon_in"))
        db.add(Store(workspace_id=ws.id, display_name="Flipkart India Store", marketplace_code="flipkart"))
        db.add(Store(workspace_id=ws.id, display_name="Meesho Supplier Store", marketplace_code="meesho"))
        db.commit()
        return [ws]
    return workspaces

@router.post("/workspaces")
def create_workspace(name: str = Form(...), db: Session = Depends(get_db)):
    ws = Workspace(name=name, subscription_tier="free")
    db.add(ws)
    db.commit()
    db.refresh(ws)
    db.add(Store(workspace_id=ws.id, display_name=f"{name} Amazon", marketplace_code="amazon_in"))
    db.add(Store(workspace_id=ws.id, display_name=f"{name} Flipkart", marketplace_code="flipkart"))
    db.add(Store(workspace_id=ws.id, display_name=f"{name} Meesho", marketplace_code="meesho"))
    db.commit()
    return ws

@router.get("/workspaces/{workspace_id}/stores")
def get_stores(workspace_id: str, db: Session = Depends(get_db)):
    stores = db.query(Store).filter(Store.workspace_id == workspace_id).all()
    if not stores:
        db.add(Store(workspace_id=workspace_id, display_name="Amazon India Store", marketplace_code="amazon_in"))
        db.add(Store(workspace_id=workspace_id, display_name="Flipkart India Store", marketplace_code="flipkart"))
        db.add(Store(workspace_id=workspace_id, display_name="Meesho Supplier Store", marketplace_code="meesho"))
        db.commit()
        stores = db.query(Store).filter(Store.workspace_id == workspace_id).all()
    return stores

# ----------------- Multi-Marketplace Ingestion -----------------
@router.post("/workspaces/{workspace_id}/imports")
async def upload_report(
    workspace_id: str,
    file: UploadFile = File(...),
    store_id: Optional[str] = Form(None),
    marketplace: Optional[str] = Form("amazon_in"),
    report_type: str = Form("settlement"),
    db: Session = Depends(get_db)
):
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB")

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    storage_filename = f"{sha256}_{file.filename}"
    file_path = os.path.join(settings.STORAGE_DIR, storage_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    if store_id:
        store = db.query(Store).filter(Store.id == store_id).first()
        if store:
            marketplace = store.marketplace_code

    import_rec = ImportRecord(
        workspace_id=workspace_id,
        store_id=store_id,
        file_name=file.filename,
        storage_path=file_path,
        sha256=sha256,
        file_size_bytes=file_size,
        mime_type=file.content_type,
        report_type=report_type,
        status="processing"
    )
    db.add(import_rec)
    db.commit()
    db.refresh(import_rec)

    try:
        raw_rows = []
        is_xlsx = file.filename.lower().endswith(".xlsx")
        
        if marketplace == "flipkart":
            if is_xlsx:
                raw_rows = FlipkartSettlementAdapter.parse_xlsx_bytes(file_bytes)
            else:
                io_str = file_bytes.decode("utf-8", errors="replace")
                raw_rows = FlipkartSettlementAdapter.parse_csv_stream(io.StringIO(io_str))
            normalizer = FlipkartSettlementAdapter.normalize_row
        elif marketplace == "meesho":
            if is_xlsx:
                raw_rows = MeeshoSettlementAdapter.parse_xlsx_bytes(file_bytes)
            else:
                io_str = file_bytes.decode("utf-8", errors="replace")
                raw_rows = MeeshoSettlementAdapter.parse_csv_stream(io.StringIO(io_str))
            normalizer = MeeshoSettlementAdapter.normalize_row
        else: # amazon_in default
            if is_xlsx:
                raw_rows = AmazonSettlementAdapter.parse_xlsx_bytes(file_bytes)
            else:
                io_str = file_bytes.decode("utf-8", errors="replace")
                raw_rows = AmazonSettlementAdapter.parse_csv_stream(io.StringIO(io_str))
            normalizer = AmazonSettlementAdapter.normalize_row

        import_rec.row_count = len(raw_rows)
        accepted = 0
        
        for r in raw_rows:
            norm = normalizer(r)
            source_rec = SourceRecord(
                workspace_id=workspace_id,
                import_id=import_rec.id,
                source_row_number=norm["source_row"] or 0,
                record_type=norm["transaction_type"],
                raw_payload=norm["raw_payload"],
                normalized_payload={
                    "order_id": norm["order_id"],
                    "sku": norm["sku"],
                    "amount": str(norm["amount"]),
                    "currency": norm["currency"]
                }
            )
            db.add(source_rec)

            if norm["order_id"]:
                st = SettlementTransaction(
                    workspace_id=workspace_id,
                    store_id=store_id,
                    import_id=import_rec.id,
                    external_order_id=norm["order_id"],
                    transaction_type=norm["transaction_type"],
                    amount=norm["amount"],
                    currency=norm["currency"],
                    source_row_number=norm["source_row"]
                )
                db.add(st)
                
                if norm["sku"]:
                    prod = db.query(Product).filter(
                        Product.workspace_id == workspace_id,
                        Product.sku == norm["sku"]
                    ).first()
                    if not prod:
                        db.add(Product(
                            workspace_id=workspace_id,
                            sku=norm["sku"],
                            title=norm["sku"],
                            cogs_amount=Decimal("0.0"),
                            packaging_cost=Decimal("0.0"),
                            shipping_estimate=Decimal("0.0")
                        ))

                existing_ord = db.query(OrderRecord).filter(
                    OrderRecord.workspace_id == workspace_id,
                    OrderRecord.external_order_id == norm["order_id"]
                ).first()
                if not existing_ord:
                    ord_record = OrderRecord(
                        workspace_id=workspace_id,
                        store_id=store_id,
                        import_id=import_rec.id,
                        external_order_id=norm["order_id"],
                        sku=norm["sku"],
                        gross_amount=norm["amount"] if norm["amount"] > 0 else Decimal("500.00"),
                        net_order_amount=norm["amount"] if norm["amount"] > 0 else Decimal("500.00"),
                        currency=norm["currency"]
                    )
                    db.add(ord_record)

            accepted += 1

        import_rec.accepted_count = accepted
        import_rec.status = "completed"
        db.commit()

    except Exception as e:
        import_rec.status = "failed"
        import_rec.error_summary = {"error": str(e)}
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "import_id": import_rec.id,
        "marketplace": marketplace,
        "file_name": import_rec.file_name,
        "row_count": import_rec.row_count,
        "accepted_count": import_rec.accepted_count,
        "status": import_rec.status
    }

@router.get("/workspaces/{workspace_id}/imports")
def get_imports(workspace_id: str, db: Session = Depends(get_db)):
    return db.query(ImportRecord).filter(ImportRecord.workspace_id == workspace_id).order_by(ImportRecord.created_at.desc()).all()

# ----------------- Customer Insight #1: Settlement-Period & Reserve Recon -----------------
@router.get("/workspaces/{workspace_id}/settlement-cycle-recon")
def get_settlement_cycle_recon(workspace_id: str, db: Session = Depends(get_db)):
    txns = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id).all()
    settlement_id = "SETTLE-AMZ-2026-W45"
    start_date = "01 Nov 2026"
    end_date = "08 Nov 2026"

    recon = SettlementCycleReconService.reconcile_settlement_cycle(
        settlement_id=settlement_id,
        start_date=start_date,
        end_date=end_date,
        marketplace="Amazon India",
        settlement_txns=txns
    )
    return recon

# ----------------- Customer Insight #2: Universal Multi-Marketplace Stacked Pivot -----------------
@router.get("/workspaces/{workspace_id}/multi-marketplace-pivot")
def get_multi_marketplace_pivot(workspace_id: str, db: Session = Depends(get_db)):
    txns = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id).all()
    stores = db.query(Store).filter(Store.workspace_id == workspace_id).all()

    pivot = MultiMarketplacePivotService.generate_stacked_pivot(
        all_settlement_txns=txns,
        all_stores=stores
    )
    return pivot

# ----------------- Customer Insight #3: Cohort Return Linking -----------------
@router.get("/workspaces/{workspace_id}/cohort-returns")
def get_cohort_returns(workspace_id: str, db: Session = Depends(get_db)):
    orders = db.query(OrderRecord).filter(OrderRecord.workspace_id == workspace_id).all()
    txns = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id).all()

    cohorts = CohortReturnLinkingService.analyze_cohort_returns(
        order_records=orders,
        settlement_txns=txns
    )
    return cohorts

# ----------------- Financial Waterfall Breakdown -----------------
@router.get("/workspaces/{workspace_id}/waterfall")
def get_financial_waterfall(workspace_id: str, db: Session = Depends(get_db)):
    txns = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id).all()
    discs = db.query(Discrepancy).filter(Discrepancy.workspace_id == workspace_id).all()
    
    gross_sales = Decimal("0.0")
    commissions = Decimal("0.0")
    shipping_fees = Decimal("0.0")
    returns_refunds = Decimal("0.0")
    discrepancies_total = sum(abs(d.difference_amount or Decimal("0.0")) for d in discs)

    for t in txns:
        amt = t.amount or Decimal("0.0")
        ttype = (t.transaction_type or "").lower()
        if "order" in ttype and amt > 0:
            gross_sales += amt
        elif "commission" in ttype or (amt < 0 and "commission" in ttype):
            commissions += abs(amt)
        elif "shipping" in ttype or "pick" in ttype:
            shipping_fees += abs(amt)
        elif "refund" in ttype or "return" in ttype:
            returns_refunds += abs(amt)

    net_bank_payout = gross_sales - commissions - shipping_fees - returns_refunds - discrepancies_total
    if net_bank_payout < 0:
        net_bank_payout = sum(t.amount for t in txns) if txns else Decimal("0.0")

    return {
        "waterfall": [
            {"name": "Gross Sales", "amount": float(gross_sales), "type": "positive"},
            {"name": "Commissions", "amount": -float(commissions), "type": "deduction"},
            {"name": "Shipping & Fulfillment", "amount": -float(shipping_fees), "type": "deduction"},
            {"name": "Customer Returns", "amount": -float(returns_refunds), "type": "deduction"},
            {"name": "Overcharges / Leakage", "amount": -float(discrepancies_total), "type": "leakage"},
            {"name": "Net Bank Settlement", "amount": float(net_bank_payout), "type": "total"}
        ],
        "found_money_total": float(discrepancies_total)
    }

# ----------------- Deterministic Reconciliation -----------------
@router.post("/workspaces/{workspace_id}/reconcile")
def run_reconciliation(workspace_id: str, store_id: Optional[str] = None, db: Session = Depends(get_db)):
    query_ords = db.query(OrderRecord).filter(OrderRecord.workspace_id == workspace_id)
    query_stls = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id)
    
    if store_id:
        query_ords = query_ords.filter(OrderRecord.store_id == store_id)
        query_stls = query_stls.filter(SettlementTransaction.store_id == store_id)

    orders = query_ords.all()
    settlements = query_stls.all()

    if not settlements:
        raise HTTPException(status_code=400, detail="No settlement transactions found. Please upload a report first.")

    run = ReconciliationRun(
        workspace_id=workspace_id,
        store_id=store_id,
        ruleset_version=ReconciliationEngine.RULESET_VERSION,
        status="completed"
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    result = ReconciliationEngine.reconcile(
        workspace_id=workspace_id,
        run_id=run.id,
        orders=orders,
        settlements=settlements
    )

    run.summary = result["summary"]
    for m in result["matches"]:
        db.add(m)
    for d in result["discrepancies"]:
        db.add(d)

    db.commit()
    db.refresh(run)

    return {
        "run_id": run.id,
        "summary": run.summary,
        "discrepancy_count": len(result["discrepancies"])
    }

@router.get("/workspaces/{workspace_id}/reconciliation/latest")
def get_latest_reconciliation(
    workspace_id: str,
    store_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ReconciliationRun).filter(ReconciliationRun.workspace_id == workspace_id)
    if store_id:
        query = query.filter(ReconciliationRun.store_id == store_id)
    run = query.order_by(ReconciliationRun.created_at.desc()).first()
    
    if not run:
        return {"run": None, "matches": [], "discrepancies": []}

    matches = db.query(ReconciliationMatch).filter(ReconciliationMatch.run_id == run.id).limit(100).all()
    discrepancies = db.query(Discrepancy).filter(Discrepancy.run_id == run.id).all()

    return {
        "run": run,
        "summary": run.summary,
        "matches": matches,
        "discrepancies": discrepancies
    }

# ----------------- Evidence Drawer Endpoint -----------------
@router.get("/workspaces/{workspace_id}/evidence/{order_id}")
def get_order_evidence(workspace_id: str, order_id: str, db: Session = Depends(get_db)):
    txns = db.query(SettlementTransaction).filter(
        SettlementTransaction.workspace_id == workspace_id,
        SettlementTransaction.external_order_id == order_id
    ).all()

    order = db.query(OrderRecord).filter(
        OrderRecord.workspace_id == workspace_id,
        OrderRecord.external_order_id == order_id
    ).first()

    sources = db.query(SourceRecord).filter(
        SourceRecord.workspace_id == workspace_id
    ).all()
    
    matched_sources = []
    for s in sources:
        if s.normalized_payload and s.normalized_payload.get("order_id") == order_id:
            matched_sources.append({
                "source_row": s.source_row_number,
                "record_type": s.record_type,
                "raw_payload": s.raw_payload,
                "normalized": s.normalized_payload
            })

    return {
        "order_id": order_id,
        "sku": order.sku if order else "N/A",
        "expected_order_net": float(order.net_order_amount) if order else 0.0,
        "actual_settlement_total": float(sum((t.amount or Decimal("0.0")) for t in txns)),
        "transactions": [
            {"type": t.transaction_type, "amount": float(t.amount), "row": t.source_row_number}
            for t in txns
        ],
        "source_rows": matched_sources
    }

# ----------------- 1-Click Dispute Ticket & Batch Manifest -----------------
@router.post("/workspaces/{workspace_id}/discrepancies/{discrepancy_id}/dispute-package")
def generate_dispute_package(
    workspace_id: str,
    discrepancy_id: str,
    seller_name: str = Form("Seller Partner"),
    db: Session = Depends(get_db)
):
    disc = db.query(Discrepancy).filter(
        Discrepancy.id == discrepancy_id,
        Discrepancy.workspace_id == workspace_id
    ).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Discrepancy not found")

    disc_data = {
        "external_order_id": disc.external_order_id,
        "category": disc.category,
        "difference_amount": disc.difference_amount,
        "source_row_number": disc.source_row_number
    }
    
    marketplace = "amazon_in"
    if disc.run and disc.run.store_id:
        st = db.query(Store).filter(Store.id == disc.run.store_id).first()
        if st:
            marketplace = st.marketplace_code

    package = DisputeGeneratorService.generate_dispute_package(
        discrepancy=disc_data,
        marketplace=marketplace,
        seller_company=seller_name
    )
    return package

@router.post("/workspaces/{workspace_id}/discrepancies/batch-manifest")
def generate_batch_dispute_manifest(
    workspace_id: str,
    discrepancy_ids: List[str] = Body(...),
    db: Session = Depends(get_db)
):
    discs = db.query(Discrepancy).filter(
        Discrepancy.workspace_id == workspace_id,
        Discrepancy.id.in_(discrepancy_ids)
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["SellerFlow AI - Batch Dispute Claim Manifest"])
    writer.writerow(["Generated At", "UTC"])
    writer.writerow([])
    writer.writerow(["Order ID", "Category", "Dispute Amount (INR)", "Source Row", "Status", "Claim Summary"])

    for d in discs:
        oid = f"'{d.external_order_id}" if str(d.external_order_id).startswith(("=", "+", "-", "@")) else d.external_order_id
        writer.writerow([
            oid,
            d.category,
            f"{abs(float(d.difference_amount or 0)):.2f}",
            d.source_row_number or "N/A",
            d.status,
            d.explanation
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=Batch_Dispute_Claim_Manifest.csv"}
    )

# ----------------- Return Leakage -----------------
@router.get("/workspaces/{workspace_id}/returns-leakage")
def get_return_leakages(workspace_id: str, db: Session = Depends(get_db)):
    settlements = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id).all()
    orders = db.query(OrderRecord).filter(OrderRecord.workspace_id == workspace_id).all()

    leakages = ReturnLeakageDetector.audit_returns(
        settlement_txns=settlements,
        order_records=orders
    )

    total_leakage = sum(item["potential_recovery_amount"] for item in leakages)
    return {
        "total_leakage_amount": total_leakage,
        "count": len(leakages),
        "leakages": leakages
    }

# ----------------- TallyPrime XML Export -----------------
@router.get("/workspaces/{workspace_id}/export/tally-xml")
def export_tally_xml(workspace_id: str, db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    company_name = ws.name if ws else "Seller Company"
    txns = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id).all()

    if not txns:
        raise HTTPException(status_code=400, detail="No settlement transactions to export into Tally")

    xml_content = TallyExporterService.generate_tally_xml(company_name, txns)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=Tally_Voucher_{workspace_id[:8]}.xml"}
    )

# ----------------- Standard Reconciliation Export -----------------
@router.get("/workspaces/{workspace_id}/reconciliation/export")
def export_reconciliation(workspace_id: str, db: Session = Depends(get_db)):
    run = db.query(ReconciliationRun).filter(
        ReconciliationRun.workspace_id == workspace_id
    ).order_by(ReconciliationRun.created_at.desc()).first()

    if not run:
        raise HTTPException(status_code=400, detail="No reconciliation run to export")

    matches = db.query(ReconciliationMatch).filter(ReconciliationMatch.run_id == run.id).all()
    discrepancies = db.query(Discrepancy).filter(Discrepancy.run_id == run.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["SellerFlow AI - Reconciliation Export"])
    writer.writerow(["Ruleset Version", run.ruleset_version])
    writer.writerow(["Generated At", str(run.created_at)])
    writer.writerow([])
    
    writer.writerow(["Order ID", "Status", "Expected Amount (INR)", "Actual Amount (INR)", "Difference (INR)", "Rule Applied"])
    for m in matches:
        order_key = f"'{m.match_group_key}" if str(m.match_group_key).startswith(("=", "+", "-", "@")) else m.match_group_key
        writer.writerow([
            order_key,
            m.match_status,
            str(m.expected_amount),
            str(m.actual_amount),
            str(m.difference_amount),
            m.matching_rule
        ])

    writer.writerow([])
    writer.writerow(["Flagged Discrepancies"])
    writer.writerow(["Order ID", "Category", "Severity", "Status", "Discrepancy Amount", "Explanation"])
    for d in discrepancies:
        order_key = f"'{d.external_order_id}" if str(d.external_order_id).startswith(("=", "+", "-", "@")) else d.external_order_id
        writer.writerow([
            order_key,
            d.category,
            d.severity,
            d.status,
            str(d.difference_amount),
            d.explanation
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=SellerFlow_Reconciliation_{run.id[:8]}.csv"}
    )

# ----------------- Products -----------------
@router.get("/workspaces/{workspace_id}/products")
def list_products(workspace_id: str, db: Session = Depends(get_db)):
    prods = db.query(Product).filter(Product.workspace_id == workspace_id).all()
    results = []
    for p in prods:
        cogs = p.cogs_amount or Decimal("0.0")
        pkg = p.packaging_cost or Decimal("0.0")
        ship = p.shipping_estimate or Decimal("0.0")
        total_cost = cogs + pkg + ship
        is_complete = cogs > Decimal("0.0")
        results.append({
            "id": p.id,
            "sku": p.sku,
            "title": p.title,
            "cogs_amount": float(cogs),
            "packaging_cost": float(pkg),
            "shipping_estimate": float(ship),
            "total_unit_cost": float(total_cost),
            "cost_coverage": "Complete" if is_complete else "Missing COGS",
            "currency": p.currency
        })
    return results

@router.post("/workspaces/{workspace_id}/products")
def upsert_product_cost(
    workspace_id: str,
    sku: str = Form(...),
    title: Optional[str] = Form(None),
    cogs: float = Form(0.0),
    packaging: float = Form(0.0),
    shipping: float = Form(0.0),
    db: Session = Depends(get_db)
):
    prod = db.query(Product).filter(
        Product.workspace_id == workspace_id,
        Product.sku == sku
    ).first()

    if not prod:
        prod = Product(
            workspace_id=workspace_id,
            sku=sku,
            title=title or sku,
            cogs_amount=Decimal(str(cogs)),
            packaging_cost=Decimal(str(packaging)),
            shipping_estimate=Decimal(str(shipping))
        )
        db.add(prod)
    else:
        prod.cogs_amount = Decimal(str(cogs))
        prod.packaging_cost = Decimal(str(packaging))
        prod.shipping_estimate = Decimal(str(shipping))
        if title:
            prod.title = title

    db.commit()
    db.refresh(prod)
    return prod
