"""add_pro_trial_tracking

Revision ID: 759e70fd6745
Revises: e4140a66fe2c
Create Date: 2025-12-31 15:32:25.811692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '759e70fd6745'
down_revision: Union[str, None] = 'e4140a66fe2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add has_used_pro_trial column to users table
    op.add_column('users', sa.Column('has_used_pro_trial', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('pro_trial_activated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove columns if rolling back
    op.drop_column('users', 'pro_trial_activated_at')
    op.drop_column('users', 'has_used_pro_trial')
