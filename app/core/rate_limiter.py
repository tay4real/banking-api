from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.config import get_settings

settings = get_settings()

def get_user_or_ip(request: Request) -> str:
    """
    Rate limit authenticated users by their user ID,
    anonymous requests by IP address.
    This prevents an attacker from bypassing IP limits
    by rotating IPs while staying logged in.
    """
    user = getattr(request.state, "user_id", None)
    return str(user) if user else get_remote_address(request)




limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=["200/minute"],
    storage_uri=settings.redis_url,
    enabled=not settings.debug   # disabled when DEBUG=True in .env      
)


async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please slow down.",
            "retry_after": str(exc.retry_after) if hasattr(exc, "retry_after") else "60"
        }
    )