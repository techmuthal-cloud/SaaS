import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Text, Numeric, BigInteger, DateTime, Date, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    default_currency = Column(String(3), default="INR")
    subscription_tier = Column(String(50), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stores = relationship("Store", back_populates="workspace", cascade="all, delete-orphan")
    imports = relationship("ImportRecord", back_populates="workspace", cascade="all, delete-orphan")
    reconciliation_runs = relationship("ReconciliationRun", back_populates="workspace", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="workspace", cascade="all, delete-orphan")

class Store(Base):
    __tablename__ = "stores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    marketplace_code = Column(String(50), default="amazon_in") # amazon_in, flipkart, meesho
    display_name = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="stores")
    imports = relationship("ImportRecord", back_populates="store", cascade="all, delete-orphan")

class ImportRecord(Base):
    __tablename__ = "imports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False)
    file_size_bytes = Column(BigInteger, default=0)
    mime_type = Column(String(100), nullable=True)
    report_type = Column(String(100), default="settlement")
    status = Column(String(50), default="uploaded") # uploaded, needs_mapping, processing, completed, failed
    row_count = Column(BigInteger, default=0)
    accepted_count = Column(BigInteger, default=0)
    rejected_count = Column(BigInteger, default=0)
    error_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="imports")
    store = relationship("Store", back_populates="imports")
    source_records = relationship("SourceRecord", back_populates="import_record", cascade="all, delete-orphan")

class SourceRecord(Base):
    __tablename__ = "source_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    import_id = Column(String(36), ForeignKey("imports.id"), nullable=False)
    source_row_number = Column(BigInteger, nullable=False)
    record_type = Column(String(50), nullable=False) # order, fee, refund, payout
    raw_payload = Column(JSON, nullable=False)
    normalized_payload = Column(JSON, nullable=True)
    validation_status = Column(String(50), default="valid") # valid, invalid
    created_at = Column(DateTime, default=datetime.utcnow)

    import_record = relationship("ImportRecord", back_populates="source_records")

class OrderRecord(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)
    import_id = Column(String(36), ForeignKey("imports.id"), nullable=True)
    external_order_id = Column(String(100), nullable=False, index=True)
    sku = Column(String(100), nullable=True, index=True)
    order_date = Column(DateTime, nullable=True)
    currency = Column(String(3), default="INR")
    gross_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    discount_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    tax_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    net_order_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    created_at = Column(DateTime, default=datetime.utcnow)

class SettlementTransaction(Base):
    __tablename__ = "settlement_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)
    import_id = Column(String(36), ForeignKey("imports.id"), nullable=True)
    external_order_id = Column(String(100), nullable=True, index=True)
    external_transaction_id = Column(String(100), nullable=True)
    transaction_type = Column(String(50), nullable=False) # Order, Refund, ServiceFee, Commission, ShippingCharge, Payout
    transaction_date = Column(DateTime, nullable=True)
    currency = Column(String(3), default="INR")
    amount = Column(Numeric(20, 6), nullable=False)
    source_row_number = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)
    ruleset_version = Column(String(50), default="v1.0")
    status = Column(String(50), default="completed")
    summary = Column(JSON, nullable=True) # totals, counts, discrepancies summary
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="reconciliation_runs")
    matches = relationship("ReconciliationMatch", back_populates="run", cascade="all, delete-orphan")
    discrepancies = relationship("Discrepancy", back_populates="run", cascade="all, delete-orphan")

class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    run_id = Column(String(36), ForeignKey("reconciliation_runs.id"), nullable=False)
    match_group_key = Column(String(100), nullable=False) # external_order_id
    match_status = Column(String(50), nullable=False) # matched, partial, unmatched, ambiguous
    expected_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    actual_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    difference_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    currency = Column(String(3), default="INR")
    matching_rule = Column(String(100), default="exact_order_id")
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ReconciliationRun", back_populates="matches")

class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    run_id = Column(String(36), ForeignKey("reconciliation_runs.id"), nullable=False)
    category = Column(String(50), nullable=False) # fee_overcharge, missing_payout, refund_mismatch, unmatched_order
    severity = Column(String(20), default="medium") # low, medium, high
    status = Column(String(50), default="open") # open, reviewing, resolved, dismissed
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)
    external_order_id = Column(String(100), nullable=True)
    difference_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    currency = Column(String(3), default="INR")
    source_row_number = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ReconciliationRun", back_populates="discrepancies")

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    sku = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    cogs_amount = Column(Numeric(20, 6), default=Decimal("0.0"))
    packaging_cost = Column(Numeric(20, 6), default=Decimal("0.0"))
    shipping_estimate = Column(Numeric(20, 6), default=Decimal("0.0"))
    currency = Column(String(3), default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="products")
