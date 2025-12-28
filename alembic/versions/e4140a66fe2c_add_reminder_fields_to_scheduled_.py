"""Add reminder fields to scheduled_contents

Revision ID: e4140a66fe2c
Revises: a542f38bd897
Create Date: 2025-12-28 23:21:32.359174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4140a66fe2c'
down_revision: Union[str, None] = 'a542f38bd897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reminder tracking fields to scheduled_contents
    op.add_column('scheduled_contents', sa.Column('reminder_24h_sent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('scheduled_contents', sa.Column('reminder_1h_sent', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('scheduled_contents', sa.Column('reminder_24h_sent_at', sa.DateTime(), nullable=True))
    op.add_column('scheduled_contents', sa.Column('reminder_1h_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove reminder fields
    op.drop_column('scheduled_contents', 'reminder_1h_sent_at')
    op.drop_column('scheduled_contents', 'reminder_24h_sent_at')
    op.drop_column('scheduled_contents', 'reminder_1h_sent')
    op.drop_column('scheduled_contents', 'reminder_24h_sent')
