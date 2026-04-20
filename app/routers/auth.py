from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse,
    TokenResponse, RefreshRequest, MessageResponse
)
from app.services.user_service import create_user
from app.services.auth_service import (
    authenticate_user, issue_token_pair,
    rotate_refresh_token, revoke_token
)
from app.dependencies import get_current_active_user
from app.core.rate_limiter import limiter

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Register limited to 3 per minute — prevents bulk account creation
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(request: Request, payload: UserRegister, db: Session = Depends(get_db)):
    user = create_user(db, payload)
    return user

# Stricter limit on login — 5 attempts per minute per IP/user
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    return issue_token_pair(str(user.id), user.role.value)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest):
    return await rotate_refresh_token(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_active_user)
):
    await revoke_token(token)
    return MessageResponse(message="Successfully logged out")