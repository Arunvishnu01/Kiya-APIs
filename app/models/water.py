import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WaterGoal(Base):
    __tablename__ = "water_goals"

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
    daily_target_ml: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        nullable=False,
    )
    checkpoint_ml: Mapped[int] = mapped_column(
        Integer,
        default=250,
        nullable=False,
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
    )


class WaterLogEntry(Base):
    __tablename__ = "water_log_entries"

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
    quantity_ml: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    client_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "quantity_ml > 0 AND quantity_ml <= 2000",
            name="check_water_quantity_range",
        ),
        UniqueConstraint(
            "user_id",
            "client_request_id",
            name="uq_water_log_user_client_request",
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="water_logs",
    )
