import time
import uuid
import structlog
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure stdlib logging as the base first
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

# Configure structlog to wrap stdlib — this is what fixes the .name error
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,       # now works — stdlib underneath
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()         # human-readable in development
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),  # use stdlib, not PrintLogger
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with timing, correlation ID, and outcome.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        start_time = time.perf_counter()

        logger.info(
            "request_started",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        log_fn = logger.warning if duration_ms > 1000 else logger.info
        log_fn(
            "request_completed",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Correlation-ID"] = correlation_id
        return response