"""Add observability tables for API metrics tracking

Revision ID: 006
Revises: 005
Create Date: 2024-12-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'api_request_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path', sa.String(500), nullable=False, index=True),
        sa.Column('status_code', sa.Integer(), nullable=False, index=True),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('client_ip', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('request_size_bytes', sa.Integer(), nullable=True),
        sa.Column('response_size_bytes', sa.Integer(), nullable=True),
    )

    op.create_index('ix_api_request_logs_path_timestamp', 'api_request_logs', ['path', 'timestamp'])
    op.create_index('ix_api_request_logs_status_timestamp', 'api_request_logs', ['status_code', 'timestamp'])

    op.create_table(
        'voice_session_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_user_audio_chunks', sa.Integer(), default=0),
        sa.Column('total_assistant_audio_chunks', sa.Integer(), default=0),
        sa.Column('transcription_latency_avg_ms', sa.Float(), nullable=True),
        sa.Column('tts_latency_avg_ms', sa.Float(), nullable=True),
        sa.Column('llm_latency_avg_ms', sa.Float(), nullable=True),
        sa.Column('total_user_words', sa.Integer(), default=0),
        sa.Column('total_assistant_words', sa.Integer(), default=0),
        sa.Column('interruptions_count', sa.Integer(), default=0),
        sa.Column('errors_count', sa.Integer(), default=0),
        sa.Column('error_messages', postgresql.JSON(), default=list),
        sa.Column('voice_id', sa.String(100), nullable=True),
        sa.Column('journal_type', sa.String(50), nullable=True),
    )

    op.create_table(
        'daily_metrics_aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.DateTime(), nullable=False, index=True, unique=True),
        sa.Column('total_requests', sa.Integer(), default=0),
        sa.Column('total_errors', sa.Integer(), default=0),
        sa.Column('error_rate', sa.Float(), default=0.0),
        sa.Column('avg_latency_ms', sa.Float(), default=0.0),
        sa.Column('p50_latency_ms', sa.Float(), default=0.0),
        sa.Column('p95_latency_ms', sa.Float(), default=0.0),
        sa.Column('p99_latency_ms', sa.Float(), default=0.0),
        sa.Column('total_voice_sessions', sa.Integer(), default=0),
        sa.Column('avg_voice_session_duration', sa.Float(), default=0.0),
        sa.Column('unique_users', sa.Integer(), default=0),
        sa.Column('new_users', sa.Integer(), default=0),
        sa.Column('total_entries_created', sa.Integer(), default=0),
        sa.Column('total_goals_created', sa.Integer(), default=0),
        sa.Column('total_goals_completed', sa.Integer(), default=0),
        sa.Column('endpoints_breakdown', postgresql.JSON(), default=dict),
    )


def downgrade() -> None:
    op.drop_table('daily_metrics_aggregates')
    op.drop_table('voice_session_metrics')
    op.drop_index('ix_api_request_logs_status_timestamp', 'api_request_logs')
    op.drop_index('ix_api_request_logs_path_timestamp', 'api_request_logs')
    op.drop_table('api_request_logs')
