from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserRegister
from app.core.security import hash_password
from app.core.exceptions import UserExistsException
from uuid import UUID


def create_user(db: Session, payload: UserRegister) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise UserExistsException()

    if db.query(User).filter(
        User.phone_number == payload.phone_number
    ).first():
        raise UserExistsException()

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def deactivate_user(db: Session, user: User) -> None:
    user.is_active = False
    db.commit()