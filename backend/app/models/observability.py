from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class APIRequestLog(Base):
    """Tracks individual API requests for debugging and analytics."""
    __tablename__ = "api_request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False, index=True)
    status_code = Column(Integer, nullable=False, index=True)

    latency_ms = Column(Float, nullable=False)

    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)

    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)

    __table_args__ = (
        Index('ix_api_request_logs_path_timestamp', 'path', 'timestamp'),
        Index('ix_api_request_logs_status_timestamp', 'status_code', 'timestamp'),
    )


class VoiceSessionMetrics(Base):
    """Tracks voice chat session performance."""
    __tablename__ = "voice_session_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    duration_seconds = Column(Float, nullable=True)

    total_user_audio_chunks = Column(Integer, default=0)
    total_assistant_audio_chunks = Column(Integer, default=0)

    transcription_latency_avg_ms = Column(Float, nullable=True)
    tts_latency_avg_ms = Column(Float, nullable=True)
    llm_latency_avg_ms = Column(Float, nullable=True)

    total_user_words = Column(Integer, default=0)
    total_assistant_words = Column(Integer, default=0)

    interruptions_count = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_messages = Column(JSON, default=list)

    voice_id = Column(String(100), nullable=True)
    journal_type = Column(String(50), nullable=True)


class LLMCallLog(Base):
    """Tracks individual LLM calls for debugging and performance analysis."""
    __tablename__ = "llm_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    model = Column(String(100), nullable=False)
    prompt_type = Column(String(50), nullable=True)

    latency_ms = Column(Float, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    success = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)

    tool_calls_count = Column(Integer, default=0)
    iteration = Column(Integer, default=0)

    __table_args__ = (
        Index('ix_llm_call_logs_session_timestamp', 'session_id', 'timestamp'),
    )


class ToolCallLog(Base):
    """Tracks individual tool calls for debugging and performance analysis."""
    __tablename__ = "tool_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    llm_call_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    tool_name = Column(String(100), nullable=False, index=True)
    tool_args = Column(JSON, nullable=True)

    latency_ms = Column(Float, nullable=False)
    success = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)
    result_preview = Column(String(500), nullable=True)

    __table_args__ = (
        Index('ix_tool_call_logs_tool_timestamp', 'tool_name', 'timestamp'),
    )


class DailyMetricsAggregate(Base):
    """Pre-aggregated daily metrics for dashboard."""
    __tablename__ = "daily_metrics_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(DateTime, nullable=False, index=True, unique=True)

    total_requests = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)

    avg_latency_ms = Column(Float, default=0.0)
    p50_latency_ms = Column(Float, default=0.0)
    p95_latency_ms = Column(Float, default=0.0)
    p99_latency_ms = Column(Float, default=0.0)

    total_voice_sessions = Column(Integer, default=0)
    avg_voice_session_duration = Column(Float, default=0.0)

    unique_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)

    total_entries_created = Column(Integer, default=0)
    total_goals_created = Column(Integer, default=0)
    total_goals_completed = Column(Integer, default=0)

    endpoints_breakdown = Column(JSON, default=dict)
