"""Add format_name to GeneratedContent model

Revision ID: f2b3c4d5e6f7
Revises: e1a02767c419
Create Date: 2025-12-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f2b3c4d5e6f7'
down_revision: Union[str, None] = 'e1a02767c419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add format_name column to generated_contents table
    op.add_column('generated_contents', sa.Column('format_name', sa.String(), nullable=True))


def downgrade() -> None:
    # Drop format_name column
    op.drop_column('generated_contents', 'format_name')
