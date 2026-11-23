"""complete schema adding 14 missing tables and user clerk columns

Revision ID: 002_complete_schema
Revises: 001_initial_schema
Create Date: 2026-11-23 12:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_complete_schema'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update users table with clerk_id and is_superuser
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('clerk_id', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('is_superuser', sa.Boolean, server_default='0', nullable=False))
        batch_op.create_index('ix_users_clerk_id', ['clerk_id'], unique=True)

    # 2. Stores
    op.create_table(
        'stores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('marketplace_code', sa.String(50), server_default='amazon_in', nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_stores_workspace_id', 'stores', ['workspace_id'])

    # 3. Imports
    op.create_table(
        'imports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('store_id', sa.String(36), sa.ForeignKey('stores.id'), nullable=True),
        sa.Column('job_id', sa.String(36), nullable=True),
        sa.Column('idempotency_key', sa.String(128), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.Text, nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger, server_default='0'),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('report_type', sa.String(100), server_default='settlement'),
        sa.Column('status', sa.String(50), server_default='uploaded'),
        sa.Column('row_count', sa.BigInteger, server_default='0'),
        sa.Column('accepted_count', sa.BigInteger, server_default='0'),
        sa.Column('rejected_count', sa.BigInteger, server_default='0'),
        sa.Column('error_summary', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('processed_at', sa.DateTime, nullable=True)
    )
    op.create_index('ix_imports_workspace_id', 'imports', ['workspace_id'])
    op.create_index('ix_imports_store_id', 'imports', ['store_id'])
    op.create_index('ix_imports_sha256', 'imports', ['sha256'])

    # 4. Source Records
    op.create_table(
        'source_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('import_id', sa.String(36), sa.ForeignKey('imports.id'), nullable=False),
        sa.Column('source_row_number', sa.BigInteger, nullable=False),
        sa.Column('record_type', sa.String(50), nullable=False),
        sa.Column('raw_payload', sa.JSON, nullable=False),
        sa.Column('normalized_payload', sa.JSON, nullable=True),
        sa.Column('validation_status', sa.String(50), server_default='valid'),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_source_records_workspace_id', 'source_records', ['workspace_id'])
    op.create_index('ix_source_records_import_id', 'source_records', ['import_id'])

    # 5. Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('store_id', sa.String(36), sa.ForeignKey('stores.id'), nullable=True),
        sa.Column('import_id', sa.String(36), sa.ForeignKey('imports.id'), nullable=True),
        sa.Column('external_order_id', sa.String(100), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        sa.Column('order_date', sa.DateTime, nullable=True),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('gross_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('tax_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('net_order_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_orders_workspace_id', 'orders', ['workspace_id'])
    op.create_index('ix_orders_external_order_id', 'orders', ['external_order_id'])
    op.create_index('ix_orders_sku', 'orders', ['sku'])

    # 6. Settlement Transactions
    op.create_table(
        'settlement_transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('store_id', sa.String(36), sa.ForeignKey('stores.id'), nullable=True),
        sa.Column('import_id', sa.String(36), sa.ForeignKey('imports.id'), nullable=True),
        sa.Column('external_order_id', sa.String(100), nullable=True),
        sa.Column('external_transaction_id', sa.String(100), nullable=True),
        sa.Column('settlement_id', sa.String(100), nullable=True),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('amount_type', sa.String(50), nullable=True),
        sa.Column('amount_description', sa.String(255), nullable=True),
        sa.Column('transaction_date', sa.DateTime, nullable=True),
        sa.Column('posted_date', sa.DateTime, nullable=True),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('source_row_number', sa.BigInteger, nullable=True),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_settlement_transactions_workspace_id', 'settlement_transactions', ['workspace_id'])
    op.create_index('ix_settlement_transactions_external_order_id', 'settlement_transactions', ['external_order_id'])
    op.create_index('ix_settlement_transactions_settlement_id', 'settlement_transactions', ['settlement_id'])

    # 7. Reconciliation Runs
    op.create_table(
        'reconciliation_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('store_id', sa.String(36), sa.ForeignKey('stores.id'), nullable=True),
        sa.Column('ruleset_version', sa.String(50), server_default='v1.0.0-deterministic'),
        sa.Column('rate_card_version', sa.String(50), server_default='2026-v1'),
        sa.Column('status', sa.String(50), server_default='completed'),
        sa.Column('summary', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_reconciliation_runs_workspace_id', 'reconciliation_runs', ['workspace_id'])

    # 8. Reconciliation Matches
    op.create_table(
        'reconciliation_matches',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('reconciliation_runs.id'), nullable=False),
        sa.Column('match_group_key', sa.String(100), nullable=False),
        sa.Column('match_status', sa.String(50), nullable=False),
        sa.Column('expected_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('actual_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('difference_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('matching_rule', sa.String(100), server_default='like_for_like_fee_audit'),
        sa.Column('evidence', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_reconciliation_matches_workspace_id', 'reconciliation_matches', ['workspace_id'])
    op.create_index('ix_reconciliation_matches_run_id', 'reconciliation_matches', ['run_id'])

    # 9. Discrepancies
    op.create_table(
        'discrepancies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('reconciliation_runs.id'), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), server_default='medium'),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('explanation', sa.Text, nullable=True),
        sa.Column('external_order_id', sa.String(100), nullable=True),
        sa.Column('difference_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('source_row_number', sa.BigInteger, nullable=True),
        sa.Column('evidence_payload', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_discrepancies_workspace_id', 'discrepancies', ['workspace_id'])
    op.create_index('ix_discrepancies_run_id', 'discrepancies', ['run_id'])
    op.create_index('ix_discrepancies_category', 'discrepancies', ['category'])

    # 10. Bank Accounts
    op.create_table(
        'bank_accounts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('bank_name', sa.String(100), nullable=False),
        sa.Column('account_number_mask', sa.String(20), nullable=False),
        sa.Column('ifsc_code', sa.String(20), nullable=True),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_bank_accounts_workspace_id', 'bank_accounts', ['workspace_id'])

    # 11. Bank Transactions
    op.create_table(
        'bank_transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('bank_account_id', sa.String(36), sa.ForeignKey('bank_accounts.id'), nullable=False),
        sa.Column('value_date', sa.Date, nullable=False),
        sa.Column('narration', sa.Text, nullable=False),
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('debit_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('credit_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('balance', sa.Numeric(18, 2), nullable=True),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_bank_transactions_workspace_id', 'bank_transactions', ['workspace_id'])
    op.create_index('ix_bank_transactions_bank_account_id', 'bank_transactions', ['bank_account_id'])
    op.create_index('ix_bank_transactions_value_date', 'bank_transactions', ['value_date'])

    # 12. Settlement Bank Matches
    op.create_table(
        'settlement_bank_matches',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('settlement_id', sa.String(100), nullable=False),
        sa.Column('bank_transaction_id', sa.String(36), sa.ForeignKey('bank_transactions.id'), nullable=False),
        sa.Column('match_status', sa.String(50), server_default='matched'),
        sa.Column('settlement_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('bank_credit_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('difference_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('match_rule', sa.String(100), server_default='exact_utr_and_amount'),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_settlement_bank_matches_workspace_id', 'settlement_bank_matches', ['workspace_id'])
    op.create_index('ix_settlement_bank_matches_settlement_id', 'settlement_bank_matches', ['settlement_id'])

    # 13. Tax Deductions
    op.create_table(
        'tax_deductions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('store_id', sa.String(36), sa.ForeignKey('stores.id'), nullable=True),
        sa.Column('tax_type', sa.String(20), nullable=False),
        sa.Column('assessment_year', sa.String(10), nullable=False),
        sa.Column('period_month', sa.String(7), nullable=False),
        sa.Column('gross_taxable_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('tax_rate', sa.Numeric(5, 4), nullable=False),
        sa.Column('tax_deducted_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('source_reference', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_tax_deductions_workspace_id', 'tax_deductions', ['workspace_id'])

    # 14. Products
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('category', sa.String(100), server_default='General'),
        sa.Column('weight_grams', sa.BigInteger, server_default='500'),
        sa.Column('cogs_amount', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('packaging_cost', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('shipping_estimate', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('currency', sa.String(3), server_default='INR'),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_products_workspace_id', 'products', ['workspace_id'])
    op.create_index('ix_products_sku', 'products', ['sku'])

    # 15. Audit Events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime)
    )
    op.create_index('ix_audit_events_workspace_id', 'audit_events', ['workspace_id'])
    op.create_index('ix_audit_events_action', 'audit_events', ['action'])

def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('products')
    op.drop_table('tax_deductions')
    op.drop_table('settlement_bank_matches')
    op.drop_table('bank_transactions')
    op.drop_table('bank_accounts')
    op.drop_table('discrepancies')
    op.drop_table('reconciliation_matches')
    op.drop_table('reconciliation_runs')
    op.drop_table('settlement_transactions')
    op.drop_table('orders')
    op.drop_table('source_records')
    op.drop_table('imports')
    op.drop_table('stores')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_clerk_id')
        batch_op.drop_column('is_superuser')
        batch_op.drop_column('clerk_id')
