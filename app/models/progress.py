import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WeightLogEntry(Base):
    __tablename__ = "weight_log_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight_kg: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    measured_on: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "weight_kg > 0 AND weight_kg <= 500",
            name="check_weight_range",
        ),
        UniqueConstraint(
            "user_id",
            "measured_on",
            name="uq_weight_log_user_measured_on",
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="weight_logs",
    )
