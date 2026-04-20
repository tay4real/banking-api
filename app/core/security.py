from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
import bcrypt
from jose import JWTError, jwt
from app.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.
    rounds=12 means 2^12 iterations — strong enough for financial systems
    without being too slow for real-time login requests.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> tuple[str, str]:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "role": role,
        "jti": jti,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def create_refresh_token(subject: str) -> tuple[str, str]:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": subject,
        "jti": jti,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm]
    )