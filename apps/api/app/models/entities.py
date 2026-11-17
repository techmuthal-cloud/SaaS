import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Text, Numeric, BigInteger, DateTime, Date, ForeignKey, JSON, Boolean, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("WorkspaceMember", back_populates="user", cascade="all, delete-orphan")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    default_currency = Column(String(3), default="INR")
    subscription_tier = Column(String(50), default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="workspace", cascade="all, delete-orphan")
    imports = relationship("ImportRecord", back_populates="workspace", cascade="all, delete-orphan")
    reconciliation_runs = relationship("ReconciliationRun", back_populates="workspace", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="workspace", cascade="all, delete-orphan")
    bank_accounts = relationship("BankAccount", back_populates="workspace", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(50), default="member") # owner, admin, accountant, member, viewer
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        Index("idx_ws_user", "workspace_id", "user_id", unique=True),
    )

class Store(Base):
    __tablename__ = "stores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    marketplace_code = Column(String(50), default="amazon_in") # amazon_in, flipkart, meesho
    display_name = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="stores")
    imports = relationship("ImportRecord", back_populates="store", cascade="all, delete-orphan")

class RateCard(Base):
    __tablename__ = "rate_cards"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    marketplace_code = Column(String(50), nullable=False, index=True) # amazon_in, flipkart, meesho
    version = Column(String(50), nullable=False) # e.g. "2026-v1"
    name = Column(String(255), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    rules = relationship("RateCardRule", back_populates="rate_card", cascade="all, delete-orphan")

class RateCardRule(Base):
    __tablename__ = "rate_card_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rate_card_id = Column(String(36), ForeignKey("rate_cards.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True) # e.g. "Furniture", "Electronics", "Apparel"
    min_price = Column(Numeric(18, 2), default=Decimal("0.0"))
    max_price = Column(Numeric(18, 2), nullable=True)
    max_weight_grams = Column(BigInteger, default=500)
    referral_fee_percent = Column(Numeric(6, 4), default=Decimal("0.1000")) # 10.0%
    closing_fee = Column(Numeric(18, 2), default=Decimal("20.00"))
    weight_handling_fee = Column(Numeric(18, 2), default=Decimal("60.00"))
    pick_pack_fee = Column(Numeric(18, 2), default=Decimal("15.00"))

    rate_card = relationship("RateCard", back_populates="rules")

class ImportRecord(Base):
    __tablename__ = "imports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True, index=True)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(BigInteger, default=0)
    mime_type = Column(String(100), nullable=True)
    report_type = Column(String(100), default="settlement")
    status = Column(String(50), default="uploaded") # uploaded, processing, completed, failed
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
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    import_id = Column(String(36), ForeignKey("imports.id"), nullable=False, index=True)
    source_row_number = Column(BigInteger, nullable=False)
    record_type = Column(String(50), nullable=False) # order, fee, refund, payout, adjustment
    raw_payload = Column(JSON, nullable=False)
    normalized_payload = Column(JSON, nullable=True)
    validation_status = Column(String(50), default="valid") # valid, invalid
    created_at = Column(DateTime, default=datetime.utcnow)

    import_record = relationship("ImportRecord", back_populates="source_records")

class OrderRecord(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True, index=True)
    import_id = Column(String(36), ForeignKey("imports.id"), nullable=True)
    external_order_id = Column(String(100), nullable=False, index=True)
    sku = Column(String(100), nullable=True, index=True)
    order_date = Column(DateTime, nullable=True)
    currency = Column(String(3), default="INR")
    gross_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    discount_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    tax_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    net_order_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    created_at = Column(DateTime, default=datetime.utcnow)

class SettlementTransaction(Base):
    __tablename__ = "settlement_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True, index=True)
    import_id = Column(String(36), ForeignKey("imports.id"), nullable=True)
    external_order_id = Column(String(100), nullable=True, index=True)
    external_transaction_id = Column(String(100), nullable=True)
    settlement_id = Column(String(100), nullable=True, index=True)
    transaction_type = Column(String(50), nullable=False) # Order, Refund, Commission, Shipping, ClosingFee, Payout, ReserveHold, ReserveRelease
    amount_type = Column(String(50), nullable=True) # ItemPrice, ItemFees, Promotion, Other
    amount_description = Column(String(255), nullable=True)
    transaction_date = Column(DateTime, nullable=True)
    posted_date = Column(DateTime, nullable=True)
    currency = Column(String(3), default="INR")
    amount = Column(Numeric(18, 2), nullable=False)
    source_row_number = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)
    ruleset_version = Column(String(50), default="v1.0.0-deterministic")
    rate_card_version = Column(String(50), default="2026-v1")
    status = Column(String(50), default="completed")
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="reconciliation_runs")
    matches = relationship("ReconciliationMatch", back_populates="run", cascade="all, delete-orphan")
    discrepancies = relationship("Discrepancy", back_populates="run", cascade="all, delete-orphan")

class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("reconciliation_runs.id"), nullable=False, index=True)
    match_group_key = Column(String(100), nullable=False, index=True)
    match_status = Column(String(50), nullable=False) # matched, partial, unmatched, ambiguous
    expected_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    actual_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    difference_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    currency = Column(String(3), default="INR")
    matching_rule = Column(String(100), default="like_for_like_fee_audit")
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ReconciliationRun", back_populates="matches")

class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("reconciliation_runs.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True) # fee_overcharge, missing_payout, return_uncredited, unmatched_order
    severity = Column(String(20), default="medium") # low, medium, high, critical
    status = Column(String(50), default="open") # open, investigating, disputed, resolved, ignored
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=True)
    external_order_id = Column(String(100), nullable=True, index=True)
    difference_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    currency = Column(String(3), default="INR")
    source_row_number = Column(BigInteger, nullable=True)
    evidence_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ReconciliationRun", back_populates="discrepancies")

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    bank_name = Column(String(100), nullable=False)
    account_number_mask = Column(String(20), nullable=False) # e.g. "XXXX-1234"
    ifsc_code = Column(String(20), nullable=True)
    currency = Column(String(3), default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="bank_accounts")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")

class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    bank_account_id = Column(String(36), ForeignKey("bank_accounts.id"), nullable=False, index=True)
    value_date = Column(Date, nullable=False, index=True)
    narration = Column(Text, nullable=False)
    reference_number = Column(String(100), nullable=True, index=True)
    debit_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    credit_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    balance = Column(Numeric(18, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bank_account = relationship("BankAccount", back_populates="transactions")

class SettlementBankMatch(Base):
    __tablename__ = "settlement_bank_matches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    settlement_id = Column(String(100), nullable=False, index=True)
    bank_transaction_id = Column(String(36), ForeignKey("bank_transactions.id"), nullable=False, index=True)
    match_status = Column(String(50), default="matched") # matched, partial, variance
    settlement_amount = Column(Numeric(18, 2), nullable=False)
    bank_credit_amount = Column(Numeric(18, 2), nullable=False)
    difference_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    match_rule = Column(String(100), default="exact_utr_and_amount")
    created_at = Column(DateTime, default=datetime.utcnow)

class TaxDeduction(Base):
    __tablename__ = "tax_deductions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    store_id = Column(String(36), ForeignKey("stores.id"), nullable=True)
    tax_type = Column(String(20), nullable=False) # TDS_194O, GST_TCS
    assessment_year = Column(String(10), nullable=False)
    period_month = Column(String(7), nullable=False) # "2026-11"
    gross_taxable_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    tax_rate = Column(Numeric(5, 4), nullable=False) # e.g. 0.0100 for 1%
    tax_deducted_amount = Column(Numeric(18, 2), nullable=False)
    source_reference = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False, index=True) # IMPORT_UPLOAD, RECON_RUN, CLAIM_GENERATE, EXPORT_TALLY
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="audit_events")

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    category = Column(String(100), default="General")
    weight_grams = Column(BigInteger, default=500)
    cogs_amount = Column(Numeric(18, 2), default=Decimal("0.0"))
    packaging_cost = Column(Numeric(18, 2), default=Decimal("0.0"))
    shipping_estimate = Column(Numeric(18, 2), default=Decimal("0.0"))
    currency = Column(String(3), default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="products")
