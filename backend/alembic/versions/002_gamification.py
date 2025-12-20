"""Add gamification and scheduled journaling

Revision ID: 002
Revises: 001
Create Date: 2024-12-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))

    op.add_column('entries', sa.Column('journal_type', sa.String(20), nullable=True))
    op.create_index('idx_entries_journal_type', 'entries', ['journal_type'])

    op.add_column('goals', sa.Column('journaling_schedule', sa.String(50), nullable=True))

    op.create_table(
        'user_achievements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('achievement_key', sa.String(50), nullable=False, index=True),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'achievement_key', name='uq_user_achievement'),
    )

    op.create_table(
        'xp_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('xp_amount', sa.Integer(), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table('xp_events')
    op.drop_table('user_achievements')

    op.drop_column('goals', 'journaling_schedule')

    op.drop_index('idx_entries_journal_type', table_name='entries')
    op.drop_column('entries', 'journal_type')

    op.drop_column('users', 'level')
    op.drop_column('users', 'total_xp')
