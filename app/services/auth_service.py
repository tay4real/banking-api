from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.redis_client import blacklist_token, is_token_blacklisted
from app.core.exceptions import (
    CredentialsException,
    InactiveUserException,
    TokenBlacklistedException
)
from app.schemas.user import TokenResponse
from app.services.user_service import get_user_by_email
from jose import JWTError


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify credentials and return the user. Timing-safe."""
    user = get_user_by_email(db, email)

    dummy_hash = "$2b$12$KIXtfM3b1aB4Y7Vbq5T3.OKmL8aH2aJcY3XmC9dM4E5fT6gN7hP8i"
    password_valid = verify_password(
        password,
        user.hashed_password if user else dummy_hash
    )

    if not user or not password_valid:
        raise CredentialsException("Invalid email or password")

    if not user.is_active:
        raise InactiveUserException()

    return user


def issue_token_pair(user_id: str, role: str) -> TokenResponse:
    """Create a fresh access + refresh token pair."""
    access_token, _ = create_access_token(subject=user_id, role=role)
    refresh_token, _ = create_refresh_token(subject=user_id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


async def rotate_refresh_token(refresh_token: str) -> TokenResponse:
    """Validate, blacklist the old refresh token, and issue a new pair."""
    try:
        token_data = decode_token(refresh_token)
    except JWTError:
        raise CredentialsException("Invalid refresh token")

    if token_data.get("type") != "refresh":
        raise CredentialsException("Invalid token type")

    jti = token_data.get("jti")
    if await is_token_blacklisted(jti):
        raise TokenBlacklistedException()

    exp = token_data.get("exp")
    ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
    await blacklist_token(jti, ttl)

    return await issue_token_pair(
        user_id=token_data["sub"],
        role=token_data.get("role", "customer")
    )


async def revoke_token(token: str) -> None:
    """Blacklist an access token on logout."""
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await blacklist_token(jti, ttl)
    except JWTError:
        pass