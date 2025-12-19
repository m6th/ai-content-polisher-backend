"""Add scheduled_content table for editorial calendar

Revision ID: g3h4i5j6k7l8
Revises: f2b3c4d5e6f7
Create Date: 2025-12-19 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g3h4i5j6k7l8'
down_revision: Union[str, None] = 'f2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scheduled_contents table
    op.create_table(
        'scheduled_contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_request_id', sa.Integer(), nullable=True),
        sa.Column('generated_content_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['content_request_id'], ['content_requests.id'], ),
        sa.ForeignKeyConstraint(['generated_content_id'], ['generated_contents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_contents_id'), 'scheduled_contents', ['id'], unique=False)


def downgrade() -> None:
    # Drop scheduled_contents table
    op.drop_index(op.f('ix_scheduled_contents_id'), table_name='scheduled_contents')
    op.drop_table('scheduled_contents')
