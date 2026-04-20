from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.models  # noqa: F401 — registers all models with SQLAlchemy

from app.config import get_settings
from app.routers import auth, users, accounts
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.core.logging import RequestLoggingMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.sanitiser import InputSanitiserMiddleware
from app.core.error_handlers import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Attach rate limiter to app state
app.state.limiter = limiter

# --- Middleware (applied bottom-up — last added runs first) ---
app.add_middleware(InputSanitiserMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.yourdomain.com"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# --- Exception handlers ---
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# --- Routers ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production"
    }