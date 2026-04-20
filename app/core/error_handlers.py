import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import logger
from app.config import get_settings

settings = get_settings()


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Standardises all HTTP errors into a consistent shape.
    Clients always get the same structure regardless of error type.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.warning(
        "http_exception",
        correlation_id=correlation_id,
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": _status_to_error_code(exc.status_code),
            "message": exc.detail,
            "correlation_id": correlation_id,
        },
        headers=getattr(exc, "headers", None)
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Pydantic validation errors — reshape into clean field-level messages.
    Default FastAPI validation errors expose internal field paths.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
        })

    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": errors,
            "correlation_id": correlation_id,
        }
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all for unexpected exceptions.
    Logs the full traceback server-side but NEVER sends it to the client.
    Stack traces in API responses are a significant security vulnerability —
    they reveal framework versions, file paths, and internal logic.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.error(
        "unhandled_exception",
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
        exc_type=type(exc).__name__,
        traceback=traceback.format_exc(),    # logged server-side only
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please contact support.",
            "correlation_id": correlation_id,  # client can quote this to support
        }
    )


def _status_to_error_code(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_server_error",
    }.get(status_code, "error")