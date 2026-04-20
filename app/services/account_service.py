import random
import string
from decimal import Decimal
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.account import Account, AccountStatus, AccountType
from app.models.user import User
from app.core.exceptions import AccountNotFoundException
from fastapi import HTTPException, status


def generate_account_number(db: Session) -> str:
    """
    Generate a unique 10-digit NUBAN-format account number.
    Retries on collision — statistically near-impossible but
    handled correctly regardless.
    """
    while True:
        bank_code = "000"
        serial = ''.join(random.choices(string.digits, k=7))
        account_number = bank_code + serial

        exists = db.query(Account).filter(
            Account.account_number == account_number
        ).first()

        if not exists:
            return account_number


def create_account(
    db: Session,
    owner: User,
    account_type: AccountType,
    currency: str
) -> Account:
    """
    Create a new bank account for a user.
    One user can hold multiple accounts of different types.
    """
    # Enforce one account per type per user
    existing = db.query(Account).filter(
        Account.owner_id == owner.id,
        Account.account_type == account_type,
        Account.status != AccountStatus.CLOSED
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already has an active {account_type.value} account"
        )

    account = Account(
        account_number=generate_account_number(db),
        account_type=account_type,
        currency=currency,
        balance=Decimal("0.0000"),
        owner_id=owner.id,
        status=AccountStatus.ACTIVE
    )

    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_account_by_id(
    db: Session,
    account_id: UUID,
    owner_id: UUID
) -> Account:
    """
    Fetch a single account. Enforces ownership —
    a user cannot retrieve another user's account.
    """
    account = db.query(Account).filter(
        Account.id == account_id,
        Account.owner_id == owner_id
    ).first()

    if not account:
        raise AccountNotFoundException()

    return account


def get_accounts_for_user(db: Session, owner_id: UUID) -> list[Account]:
    """
    Return all non-closed accounts belonging to the user.
    """
    return db.query(Account).filter(
        Account.owner_id == owner_id,
        Account.status != AccountStatus.CLOSED
    ).all()


def freeze_account(db: Session, account_id: UUID) -> Account:
    """
    Admin operation — freeze an account.
    Frozen accounts cannot send or receive funds.
    """
    account = db.query(Account).filter(
        Account.id == account_id
    ).first()

    if not account:
        raise AccountNotFoundException()

    if account.status == AccountStatus.FROZEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already frozen"
        )

    if account.status == AccountStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot freeze a closed account"
        )

    account.status = AccountStatus.FROZEN
    db.commit()
    db.refresh(account)
    return account


def unfreeze_account(db: Session, account_id: UUID) -> Account:
    """Admin operation — restore a frozen account to active."""
    account = db.query(Account).filter(
        Account.id == account_id
    ).first()

    if not account:
        raise AccountNotFoundException()

    if account.status != AccountStatus.FROZEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not frozen"
        )

    account.status = AccountStatus.ACTIVE
    db.commit()
    db.refresh(account)
    return account