import uuid
from sqlalchemy import Column, String, Enum, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.database import Base
from app.models import TimestampMixin


class AccountType(str, enum.Enum):
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"
    PENDING = "pending"


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    account_number = Column(
        String(10),
        unique=True,
        index=True,
        nullable=False
    )
    account_type = Column(
        Enum(AccountType),
        default=AccountType.SAVINGS,
        nullable=False
    )
    status = Column(
        Enum(AccountStatus),
        default=AccountStatus.PENDING,
        nullable=False
    )
    balance = Column(
        Numeric(precision=19, scale=4),
        nullable=False,
        default=0
    )
    currency = Column(String(3), nullable=False, default="NGN")
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Relationship
    owner = relationship("User", back_populates="accounts")

    # Database-level constraint: balance can never go negative
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_account_balance_non_negative"),
    )

    def __repr__(self):
        return f"<Account {self.account_number}>"