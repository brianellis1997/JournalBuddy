import time
import logging
from typing import Callable
from uuid import UUID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.database import async_session_maker
from app.models.observability import APIRequestLog
from app.core.security import decode_token

logger = logging.getLogger(__name__)


SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}
SKIP_PREFIXES = ("/api/v1/observability",)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in SKIP_PATHS or any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        start_time = time.perf_counter()

        user_id = None
        error_message = None
        error_type = None
        status_code = 500

        try:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    payload = decode_token(token)
                    if payload:
                        user_id_str = payload.get("sub")
                        if user_id_str:
                            user_id = UUID(user_id_str)
                except Exception:
                    pass

            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            logger.exception(f"Request error: {request.url.path}")
            raise

        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000

            try:
                await self._log_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    error_message=error_message,
                    error_type=error_type,
                    request_size=int(request.headers.get("Content-Length", 0)),
                )
            except Exception as log_error:
                logger.warning(f"Failed to log request: {log_error}")

        return response

    async def _log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        user_id: UUID | None,
        client_ip: str | None,
        user_agent: str | None,
        error_message: str | None,
        error_type: str | None,
        request_size: int,
    ):
        async with async_session_maker() as session:
            log_entry = APIRequestLog(
                method=method,
                path=path,
                status_code=status_code,
                latency_ms=latency_ms,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent[:500] if user_agent else None,
                error_message=error_message,
                error_type=error_type,
                request_size_bytes=request_size,
            )
            session.add(log_entry)
            await session.commit()
