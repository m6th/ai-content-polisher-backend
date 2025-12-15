"""add_is_admin_field

Revision ID: 90391a34f26e
Revises: 1837f7fb6221
Create Date: 2025-12-11 13:39:44.573888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90391a34f26e'
down_revision: Union[str, None] = '1837f7fb6221'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column
    op.add_column('users', sa.Column('is_admin', sa.Integer(), nullable=True))

    # Set default value for existing users (all non-admin by default)
    op.execute("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL")


def downgrade() -> None:
    op.drop_column('users', 'is_admin')
