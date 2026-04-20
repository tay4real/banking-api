from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.core.redis_client import is_token_blacklisted
from app.core.exceptions import CredentialsException, TokenBlacklistedException, InactiveUserException
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_token(token)
    except JWTError:
        raise CredentialsException()

    # Verify token type
    if payload.get("type") != "access":
        raise CredentialsException("Invalid token type")

    # Check blacklist
    jti = payload.get("jti")
    if not jti or await is_token_blacklisted(jti):
        raise TokenBlacklistedException()

    # Load user from DB
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise CredentialsException()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise CredentialsException("Admin access required")
    return current_user