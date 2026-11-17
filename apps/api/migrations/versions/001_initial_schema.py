"""initial schema with tenant isolation, rate cards and bank reconciliation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-17 22:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('default_currency', sa.String(3), server_default='INR'),
        sa.Column('subscription_tier', sa.String(50), server_default='free'),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime)
    )

    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='1'),
        sa.Column('created_at', sa.DateTime)
    )

    # Workspace Members (Tenant Isolation)
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(36), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(50), server_default='member'),
        sa.Column('created_at', sa.DateTime),
        sa.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member')
    )

    # Rate Cards
    op.create_table(
        'rate_cards',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('marketplace_code', sa.String(50), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('effective_from', sa.Date, nullable=False),
        sa.Column('effective_to', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime)
    )

    # Rate Card Rules
    op.create_table(
        'rate_card_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('rate_card_id', sa.String(36), sa.ForeignKey('rate_cards.id'), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('min_price', sa.Numeric(18, 2), server_default='0.00'),
        sa.Column('max_price', sa.Numeric(18, 2), nullable=True),
        sa.Column('max_weight_grams', sa.BigInteger, server_default='500'),
        sa.Column('referral_fee_percent', sa.Numeric(6, 4), server_default='0.1000'),
        sa.Column('closing_fee', sa.Numeric(18, 2), server_default='20.00'),
        sa.Column('weight_handling_fee', sa.Numeric(18, 2), server_default='60.00'),
        sa.Column('pick_pack_fee', sa.Numeric(18, 2), server_default='15.00')
    )

def downgrade() -> None:
    op.drop_table('rate_card_rules')
    op.drop_table('rate_cards')
    op.drop_table('workspace_members')
    op.drop_table('users')
    op.drop_table('workspaces')
