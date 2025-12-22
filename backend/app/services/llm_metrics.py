import time
import logging
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Any
from contextlib import asynccontextmanager

from app.core.database import async_session_maker
from app.models.observability import LLMCallLog, ToolCallLog

logger = logging.getLogger(__name__)


class LLMMetricsTracker:
    def __init__(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        model: str = "unknown",
        prompt_type: str = None,
    ):
        self.session_id = UUID(session_id) if session_id else None
        self.user_id = UUID(user_id) if user_id else None
        self.model = model
        self.prompt_type = prompt_type
        self._current_llm_call_id: Optional[UUID] = None

    @asynccontextmanager
    async def track_llm_call(self, iteration: int = 0):
        """Context manager to track an LLM call."""
        start_time = time.perf_counter()
        llm_call_id = uuid4()
        self._current_llm_call_id = llm_call_id

        result = {
            "success": True,
            "error_message": None,
            "error_type": None,
            "tool_calls_count": 0,
            "input_tokens": None,
            "output_tokens": None,
        }

        try:
            yield result
        except Exception as e:
            result["success"] = False
            result["error_message"] = str(e)[:1000]
            result["error_type"] = type(e).__name__
            raise
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000

            try:
                async with async_session_maker() as db:
                    log = LLMCallLog(
                        id=llm_call_id,
                        session_id=self.session_id,
                        user_id=self.user_id,
                        model=self.model,
                        prompt_type=self.prompt_type,
                        latency_ms=latency_ms,
                        input_tokens=result.get("input_tokens"),
                        output_tokens=result.get("output_tokens"),
                        total_tokens=(result.get("input_tokens") or 0) + (result.get("output_tokens") or 0) or None,
                        success=1 if result["success"] else 0,
                        error_message=result.get("error_message"),
                        error_type=result.get("error_type"),
                        tool_calls_count=result.get("tool_calls_count", 0),
                        iteration=iteration,
                    )
                    db.add(log)
                    await db.commit()
            except Exception as log_err:
                logger.warning(f"Failed to log LLM call: {log_err}")

    @asynccontextmanager
    async def track_tool_call(self, tool_name: str, tool_args: dict = None):
        """Context manager to track a tool call."""
        start_time = time.perf_counter()

        result = {
            "success": True,
            "error_message": None,
            "result_preview": None,
        }

        try:
            yield result
        except Exception as e:
            result["success"] = False
            result["error_message"] = str(e)[:1000]
            raise
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000

            try:
                async with async_session_maker() as db:
                    safe_args = None
                    if tool_args:
                        safe_args = {k: str(v)[:200] if isinstance(v, str) else v for k, v in tool_args.items()}

                    log = ToolCallLog(
                        llm_call_id=self._current_llm_call_id,
                        session_id=self.session_id,
                        user_id=self.user_id,
                        tool_name=tool_name,
                        tool_args=safe_args,
                        latency_ms=latency_ms,
                        success=1 if result["success"] else 0,
                        error_message=result.get("error_message"),
                        result_preview=result.get("result_preview"),
                    )
                    db.add(log)
                    await db.commit()
            except Exception as log_err:
                logger.warning(f"Failed to log tool call: {log_err}")

    async def log_tool_call_sync(
        self,
        tool_name: str,
        tool_args: dict,
        latency_ms: float,
        success: bool = True,
        error_message: str = None,
        result_preview: str = None,
    ):
        """Log a tool call directly (for cases where context manager isn't suitable)."""
        try:
            async with async_session_maker() as db:
                safe_args = None
                if tool_args:
                    safe_args = {k: str(v)[:200] if isinstance(v, str) else v for k, v in tool_args.items()}

                log = ToolCallLog(
                    llm_call_id=self._current_llm_call_id,
                    session_id=self.session_id,
                    user_id=self.user_id,
                    tool_name=tool_name,
                    tool_args=safe_args,
                    latency_ms=latency_ms,
                    success=1 if success else 0,
                    error_message=error_message[:1000] if error_message else None,
                    result_preview=result_preview[:500] if result_preview else None,
                )
                db.add(log)
                await db.commit()
        except Exception as log_err:
            logger.warning(f"Failed to log tool call: {log_err}")
