from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class TimestampMixin:
    """Adds created_at, updated_at, and soft-delete to every model."""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)


# Import both models here so SQLAlchemy's registry sees them together
from app.models.user import User        # noqa: F401
from app.models.account import Account  # noqa: F401

