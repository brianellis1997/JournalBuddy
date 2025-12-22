"""Add LLM and tool call tracking tables

Revision ID: 007
Revises: 006
Create Date: 2024-12-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'llm_call_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('prompt_type', sa.String(50), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('success', sa.Integer(), default=1),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('tool_calls_count', sa.Integer(), default=0),
        sa.Column('iteration', sa.Integer(), default=0),
    )
    op.create_index('ix_llm_call_logs_session_timestamp', 'llm_call_logs', ['session_id', 'timestamp'])

    op.create_table(
        'tool_call_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('llm_call_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('tool_name', sa.String(100), nullable=False, index=True),
        sa.Column('tool_args', postgresql.JSON(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('success', sa.Integer(), default=1),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result_preview', sa.String(500), nullable=True),
    )
    op.create_index('ix_tool_call_logs_tool_timestamp', 'tool_call_logs', ['tool_name', 'timestamp'])


def downgrade() -> None:
    op.drop_index('ix_tool_call_logs_tool_timestamp', 'tool_call_logs')
    op.drop_table('tool_call_logs')
    op.drop_index('ix_llm_call_logs_session_timestamp', 'llm_call_logs')
    op.drop_table('llm_call_logs')
