"""Add voice agent fields and goal progress tracking

Revision ID: 003
Revises: 002
Create Date: 2024-12-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chat_sessions', sa.Column('session_type', sa.String(20), nullable=False, server_default='text'))
    op.add_column('chat_sessions', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('chat_sessions', sa.Column('key_topics', sa.Text(), nullable=True))
    op.add_column('chat_sessions', sa.Column('goal_updates', sa.Text(), nullable=True))
    op.create_index('idx_chat_sessions_type', 'chat_sessions', ['session_type'])

    op.add_column('goals', sa.Column('progress', sa.Integer(), nullable=False, server_default='0'))

    op.create_table(
        'goal_progress_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('goals.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('previous_progress', sa.Integer(), nullable=False),
        sa.Column('new_progress', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table('goal_progress_updates')

    op.drop_column('goals', 'progress')

    op.drop_index('idx_chat_sessions_type', table_name='chat_sessions')
    op.drop_column('chat_sessions', 'goal_updates')
    op.drop_column('chat_sessions', 'key_topics')
    op.drop_column('chat_sessions', 'summary')
    op.drop_column('chat_sessions', 'session_type')
