"""add_api_keys_table

Revision ID: 0f242032f6d4
Revises: 759e70fd6745
Create Date: 2026-01-03 11:43:58.419971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f242032f6d4'
down_revision: Union[str, None] = '759e70fd6745'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),  # ex: acp_live_abc123
        sa.Column('key_hash', sa.String(255), nullable=False),  # Hash SHA256 de la clé complète
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_key_prefix', 'api_keys', ['key_prefix'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_api_keys_key_prefix', 'api_keys')
    op.drop_index('idx_api_keys_user_id', 'api_keys')
    op.drop_table('api_keys')
