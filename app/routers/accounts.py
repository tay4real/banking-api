from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.account import (
    AccountCreate,
    AccountResponse,
    AccountBalanceResponse,
    AccountListResponse
)
from app.services.account_service import (
    create_account,
    get_account_by_id,
    get_accounts_for_user,
    freeze_account,
    unfreeze_account
)
from app.dependencies import get_current_active_user, require_admin

router = APIRouter()


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED
)
def create_new_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return create_account(
        db=db,
        owner=current_user,
        account_type=payload.account_type,
        currency=payload.currency
    )


@router.get("", response_model=AccountListResponse)
def list_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    accounts = get_accounts_for_user(db=db, owner_id=current_user.id)
    return AccountListResponse(
        total=len(accounts),
        accounts=accounts
    )


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return get_account_by_id(
        db=db,
        account_id=account_id,
        owner_id=current_user.id
    )


@router.get("/{account_id}/balance", response_model=AccountBalanceResponse)
def get_balance(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    account = get_account_by_id(
        db=db,
        account_id=account_id,
        owner_id=current_user.id
    )
    return AccountBalanceResponse(
        account_number=account.account_number,
        balance=account.balance,
        currency=account.currency,
        status=account.status,
        as_of=datetime.now(timezone.utc)
    )


@router.patch(
    "/{account_id}/freeze",
    response_model=AccountResponse
)
def freeze(
    account_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)      # _ means we need the check but not the object
):
    return freeze_account(db=db, account_id=account_id)


@router.patch(
    "/{account_id}/unfreeze",
    response_model=AccountResponse
)
def unfreeze(
    account_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    return unfreeze_account(db=db, account_id=account_id)