"""add_last_credit_renewal_field

Revision ID: 5b504faa0bc0
Revises: 90391a34f26e
Create Date: 2025-12-11 22:32:53.266096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b504faa0bc0'
down_revision: Union[str, None] = '90391a34f26e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_credit_renewal column
    op.add_column('users', sa.Column('last_credit_renewal', sa.DateTime(), nullable=True))

    # Set default value for existing users (use their creation date or current time)
    op.execute("UPDATE users SET last_credit_renewal = created_at WHERE last_credit_renewal IS NULL")


def downgrade() -> None:
    op.drop_column('users', 'last_credit_renewal')
