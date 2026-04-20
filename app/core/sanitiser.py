import re
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse


class InputSanitiserMiddleware(BaseHTTPMiddleware):
    """
    First line of defence against common injection patterns.
    This does NOT replace parameterised queries — SQLAlchemy
    already handles SQL injection. This catches null bytes,
    oversized payloads, and obvious XSS attempts before they
    reach your route handlers.
    """

    MAX_CONTENT_LENGTH = 1_048_576  # 1MB — reject anything larger

    # Patterns that have no place in a financial API request
    SUSPICIOUS_PATTERNS = [
        r"<script.*?>",           # XSS script tags
        r"javascript:",           # XSS javascript protocol
        r"\x00",                  # null bytes
        r"\.\./",                 # path traversal
        r"(union|select|insert|update|delete|drop)\s",  # raw SQL keywords
    ]

    COMPILED_PATTERNS = [
        re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Block oversized payloads before reading body
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=413,
                content={"error": "payload_too_large", "message": "Request body too large"}
            )

        # Check query parameters for injection patterns
        query_string = str(request.url.query)
        for pattern in self.COMPILED_PATTERNS:
            if pattern.search(query_string):
                return JSONResponse(
                    status_code=400,
                    content={"error": "invalid_input", "message": "Invalid characters in request"}
                )

        return await call_next(request)