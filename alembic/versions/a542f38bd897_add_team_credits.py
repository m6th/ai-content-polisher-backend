"""add_team_credits

Revision ID: a542f38bd897
Revises: h4i5j6k7l8m9
Create Date: 2025-12-27 00:27:40.088210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a542f38bd897'
down_revision: Union[str, None] = 'h4i5j6k7l8m9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add team_credits column to teams table
    op.add_column('teams', sa.Column('team_credits', sa.Integer(), nullable=False, server_default='0'))

    # Set default credits based on plan
    # Pro teams: 150 credits, Business teams: 500 credits
    op.execute("""
        UPDATE teams
        SET team_credits = CASE
            WHEN plan = 'pro' THEN 150
            WHEN plan = 'business' THEN 500
            ELSE 0
        END
    """)


def downgrade() -> None:
    op.drop_column('teams', 'team_credits')
