import re
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from app.models.user import UserRole


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain a number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain a special character")
        return v

    @field_validator("phone_number")
    @classmethod
    def validate_nigerian_phone(cls, v: str) -> str:
        # Accept formats: 08012345678, +2348012345678, 2348012345678
        pattern = r"^(\+?234|0)[789][01]\d{8}$"
        if not re.match(pattern, v):
            raise ValueError("Enter a valid Nigerian phone number")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    phone_number: str | None
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str