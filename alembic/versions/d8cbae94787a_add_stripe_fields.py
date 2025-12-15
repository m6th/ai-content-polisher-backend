"""add_stripe_fields

Revision ID: d8cbae94787a
Revises: 5b504faa0bc0
Create Date: 2025-12-13 17:14:19.616609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8cbae94787a'
down_revision: Union[str, None] = '5b504faa0bc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Stripe columns to users table
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(), nullable=True))
    op.add_column('users', sa.Column('subscription_status', sa.String(), server_default='inactive', nullable=True))
    op.add_column('users', sa.Column('subscription_end_date', sa.DateTime(), nullable=True))

    # Create unique index on stripe_customer_id
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=True)


def downgrade() -> None:
    # Remove Stripe columns
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_column('users', 'subscription_end_date')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
