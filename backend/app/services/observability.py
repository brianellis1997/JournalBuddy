from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, func, and_, text, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import APIRequestLog, VoiceSessionMetrics, DailyMetricsAggregate, LLMCallLog, ToolCallLog


class ObservabilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_request_stats(
        self,
        hours: int = 24,
        path_filter: str | None = None
    ) -> dict:
        """Get aggregated request statistics for the past N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)

        conditions = [APIRequestLog.timestamp >= since]
        if path_filter:
            conditions.append(APIRequestLog.path.like(f"%{path_filter}%"))

        base_query = select(APIRequestLog).where(and_(*conditions))

        total_result = await self.db.execute(
            select(func.count(APIRequestLog.id)).where(and_(*conditions))
        )
        total_requests = total_result.scalar() or 0

        errors_result = await self.db.execute(
            select(func.count(APIRequestLog.id)).where(
                and_(*conditions, APIRequestLog.status_code >= 400)
            )
        )
        total_errors = errors_result.scalar() or 0

        latency_result = await self.db.execute(
            select(
                func.avg(APIRequestLog.latency_ms),
                func.percentile_cont(0.5).within_group(APIRequestLog.latency_ms),
                func.percentile_cont(0.95).within_group(APIRequestLog.latency_ms),
                func.percentile_cont(0.99).within_group(APIRequestLog.latency_ms),
            ).where(and_(*conditions))
        )
        latency_row = latency_result.fetchone()

        unique_users_result = await self.db.execute(
            select(func.count(func.distinct(APIRequestLog.user_id))).where(
                and_(*conditions, APIRequestLog.user_id.isnot(None))
            )
        )
        unique_users = unique_users_result.scalar() or 0

        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
            "avg_latency_ms": round(latency_row[0] or 0, 2),
            "p50_latency_ms": round(latency_row[1] or 0, 2),
            "p95_latency_ms": round(latency_row[2] or 0, 2),
            "p99_latency_ms": round(latency_row[3] or 0, 2),
            "unique_users": unique_users,
        }

    async def get_endpoint_breakdown(self, hours: int = 24) -> list[dict]:
        """Get request counts and latency by endpoint."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(
                APIRequestLog.path,
                func.count(APIRequestLog.id).label("count"),
                func.avg(APIRequestLog.latency_ms).label("avg_latency"),
                func.count(APIRequestLog.id).filter(
                    APIRequestLog.status_code >= 400
                ).label("errors"),
            )
            .where(APIRequestLog.timestamp >= since)
            .group_by(APIRequestLog.path)
            .order_by(func.count(APIRequestLog.id).desc())
            .limit(50)
        )

        return [
            {
                "path": row.path,
                "count": row.count,
                "avg_latency_ms": round(row.avg_latency or 0, 2),
                "errors": row.errors,
                "error_rate": round((row.errors / row.count * 100) if row.count > 0 else 0, 2),
            }
            for row in result.fetchall()
        ]

    async def get_error_breakdown(self, hours: int = 24) -> list[dict]:
        """Get error counts by type."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(
                APIRequestLog.status_code,
                APIRequestLog.error_type,
                func.count(APIRequestLog.id).label("count"),
            )
            .where(
                and_(
                    APIRequestLog.timestamp >= since,
                    APIRequestLog.status_code >= 400
                )
            )
            .group_by(APIRequestLog.status_code, APIRequestLog.error_type)
            .order_by(func.count(APIRequestLog.id).desc())
            .limit(20)
        )

        return [
            {
                "status_code": row.status_code,
                "error_type": row.error_type,
                "count": row.count,
            }
            for row in result.fetchall()
        ]

    async def get_recent_errors(self, limit: int = 20) -> list[dict]:
        """Get most recent error logs."""
        result = await self.db.execute(
            select(APIRequestLog)
            .where(APIRequestLog.status_code >= 400)
            .order_by(APIRequestLog.timestamp.desc())
            .limit(limit)
        )

        return [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "method": log.method,
                "path": log.path,
                "status_code": log.status_code,
                "latency_ms": round(log.latency_ms, 2),
                "error_type": log.error_type,
                "error_message": log.error_message[:500] if log.error_message else None,
                "user_id": str(log.user_id) if log.user_id else None,
            }
            for log in result.scalars().all()
        ]

    async def get_voice_session_stats(self, hours: int = 24) -> dict:
        """Get voice session statistics."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(
                func.count(VoiceSessionMetrics.id),
                func.avg(VoiceSessionMetrics.duration_seconds),
                func.avg(VoiceSessionMetrics.transcription_latency_avg_ms),
                func.avg(VoiceSessionMetrics.tts_latency_avg_ms),
                func.avg(VoiceSessionMetrics.llm_latency_avg_ms),
                func.sum(VoiceSessionMetrics.errors_count),
            ).where(VoiceSessionMetrics.started_at >= since)
        )

        row = result.fetchone()

        return {
            "period_hours": hours,
            "total_sessions": row[0] or 0,
            "avg_duration_seconds": round(row[1] or 0, 2),
            "avg_transcription_latency_ms": round(row[2] or 0, 2),
            "avg_tts_latency_ms": round(row[3] or 0, 2),
            "avg_llm_latency_ms": round(row[4] or 0, 2),
            "total_errors": row[5] or 0,
        }

    async def get_latency_timeseries(
        self,
        hours: int = 24,
        bucket_minutes: int = 15
    ) -> list[dict]:
        """Get latency over time bucketed by interval."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            text(f"""
                SELECT
                    date_trunc('hour', timestamp) +
                    (EXTRACT(minute FROM timestamp)::int / {bucket_minutes}) * interval '{bucket_minutes} minutes' as bucket,
                    COUNT(*) as count,
                    AVG(latency_ms) as avg_latency,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency
                FROM api_request_logs
                WHERE timestamp >= :since
                GROUP BY bucket
                ORDER BY bucket
            """),
            {"since": since}
        )

        return [
            {
                "timestamp": row.bucket.isoformat(),
                "count": row.count,
                "avg_latency_ms": round(row.avg_latency or 0, 2),
                "p95_latency_ms": round(row.p95_latency or 0, 2),
            }
            for row in result.fetchall()
        ]

    async def get_llm_stats(self, hours: int = 24) -> dict:
        """Get LLM call statistics."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(
                func.count(ToolCallLog.id),
                func.avg(ToolCallLog.latency_ms),
                func.sum(case((ToolCallLog.success == 0, 1), else_=0)),
            ).where(
                and_(
                    ToolCallLog.timestamp >= since,
                    ToolCallLog.tool_name == "_llm_call"
                )
            )
        )
        row = result.fetchone()

        return {
            "period_hours": hours,
            "total_llm_calls": row[0] or 0,
            "avg_latency_ms": round(row[1] or 0, 2),
            "total_errors": row[2] or 0,
            "error_rate": round((row[2] or 0) / (row[0] or 1) * 100, 2),
        }

    async def get_tool_stats(self, hours: int = 24) -> dict:
        """Get tool call statistics."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(
                ToolCallLog.tool_name,
                func.count(ToolCallLog.id).label("count"),
                func.avg(ToolCallLog.latency_ms).label("avg_latency"),
                func.sum(case((ToolCallLog.success == 0, 1), else_=0)).label("errors"),
            )
            .where(
                and_(
                    ToolCallLog.timestamp >= since,
                    ToolCallLog.tool_name != "_llm_call"
                )
            )
            .group_by(ToolCallLog.tool_name)
            .order_by(func.count(ToolCallLog.id).desc())
        )

        tools = []
        total_calls = 0
        total_errors = 0

        for row in result.fetchall():
            tools.append({
                "tool_name": row.tool_name,
                "count": row.count,
                "avg_latency_ms": round(row.avg_latency or 0, 2),
                "errors": row.errors or 0,
                "error_rate": round((row.errors or 0) / row.count * 100, 2) if row.count > 0 else 0,
            })
            total_calls += row.count
            total_errors += row.errors or 0

        return {
            "period_hours": hours,
            "total_tool_calls": total_calls,
            "total_errors": total_errors,
            "tools": tools,
        }

    async def get_recent_tool_calls(self, limit: int = 50, tool_name: str = None) -> list[dict]:
        """Get recent tool calls."""
        conditions = [ToolCallLog.tool_name != "_llm_call"]
        if tool_name:
            conditions.append(ToolCallLog.tool_name == tool_name)

        result = await self.db.execute(
            select(ToolCallLog)
            .where(and_(*conditions))
            .order_by(ToolCallLog.timestamp.desc())
            .limit(limit)
        )

        return [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "tool_name": log.tool_name,
                "tool_args": log.tool_args,
                "latency_ms": round(log.latency_ms, 2),
                "success": bool(log.success),
                "error_message": log.error_message,
                "result_preview": log.result_preview,
                "session_id": str(log.session_id) if log.session_id else None,
            }
            for log in result.scalars().all()
        ]

    async def get_tool_errors(self, hours: int = 24) -> list[dict]:
        """Get recent tool call errors."""
        since = datetime.utcnow() - timedelta(hours=hours)

        result = await self.db.execute(
            select(ToolCallLog)
            .where(
                and_(
                    ToolCallLog.timestamp >= since,
                    ToolCallLog.success == 0,
                    ToolCallLog.tool_name != "_llm_call"
                )
            )
            .order_by(ToolCallLog.timestamp.desc())
            .limit(50)
        )

        return [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "tool_name": log.tool_name,
                "tool_args": log.tool_args,
                "latency_ms": round(log.latency_ms, 2),
                "error_message": log.error_message,
                "session_id": str(log.session_id) if log.session_id else None,
            }
            for log in result.scalars().all()
        ]

    async def get_dashboard_summary(self) -> dict:
        """Get a complete dashboard summary."""
        return {
            "last_hour": await self.get_request_stats(hours=1),
            "last_24_hours": await self.get_request_stats(hours=24),
            "endpoints": await self.get_endpoint_breakdown(hours=24),
            "errors": await self.get_error_breakdown(hours=24),
            "recent_errors": await self.get_recent_errors(limit=10),
            "voice_sessions": await self.get_voice_session_stats(hours=24),
            "llm": await self.get_llm_stats(hours=24),
            "tools": await self.get_tool_stats(hours=24),
        }
