from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.account import AccountType, AccountStatus


class AccountCreate(BaseModel):
    account_type: AccountType = AccountType.SAVINGS
    currency: str = "NGN"

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed = {"NGN", "USD", "GBP", "EUR"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_number: str
    account_type: AccountType
    status: AccountStatus
    balance: Decimal
    currency: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class AccountBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_number: str
    balance: Decimal
    currency: str
    status: AccountStatus
    as_of: datetime


class AccountListResponse(BaseModel):
    total: int
    accounts: list[AccountResponse]