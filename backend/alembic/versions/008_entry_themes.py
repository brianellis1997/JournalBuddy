"""Add themes column to entries table

Revision ID: 008
Revises: 007
Create Date: 2024-12-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('entries', sa.Column('themes', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('entries', 'themes')
