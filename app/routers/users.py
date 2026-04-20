from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, MessageResponse
from app.dependencies import get_current_active_user, require_admin
from app.core.exceptions import UserNotFoundException
from app.services.user_service import get_user_by_id, deactivate_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    return current_user


@router.delete("/me", response_model=MessageResponse)
def deactivate_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    deactivate_user(db, current_user)
    return MessageResponse(message="Account deactivated successfully")


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Admin only — look up any user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException()
    return user