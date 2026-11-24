import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.meal import MealPlanAssignment, MealSubmission, MealReview
    from app.models.workout import WorkoutAssignment
    from app.models.water import WaterGoal, WaterLogEntry
    from app.models.progress import WeightLogEntry
    from app.models.notification import Notification
    from app.models.subscription import PlanEnrollment


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
    )
    phone_e164: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="USER",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('USER', 'COACH', 'ADMIN', 'SUPER_ADMIN')",
            name="check_user_role",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED')",
            name="check_user_status",
        ),
    )

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    goals: Mapped[List["UserGoal"]] = relationship(
        "UserGoal",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    device_tokens: Mapped[List["UserDeviceToken"]] = relationship(
        "UserDeviceToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_preference: Mapped[Optional["NotificationPreference"]] = relationship(
        "NotificationPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    meal_assignments: Mapped[List["MealPlanAssignment"]] = relationship(
        "MealPlanAssignment",
        foreign_keys="MealPlanAssignment.user_id",
        back_populates="user",
    )
    workout_assignments: Mapped[List["WorkoutAssignment"]] = relationship(
        "WorkoutAssignment",
        foreign_keys="WorkoutAssignment.user_id",
        back_populates="user",
    )
    plan_enrollments: Mapped[List["PlanEnrollment"]] = relationship(
        "PlanEnrollment",
        back_populates="user",
    )
    water_logs: Mapped[List["WaterLogEntry"]] = relationship(
        "WaterLogEntry",
        back_populates="user",
    )
    weight_logs: Mapped[List["WeightLogEntry"]] = relationship(
        "WeightLogEntry",
        back_populates="user",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="recipient",
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    height_cm: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        default="Asia/Kolkata",
        nullable=False,
    )
    activity_preference: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    avatar_object_key: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )


class UserGoal(Base):
    __tablename__ = "user_goals"

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
    goal_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="goals",
    )


class UserDeviceToken(Base):
    __tablename__ = "user_device_tokens"

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
    device_platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    fcm_token: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="device_tokens",
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    push_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    meal_reminders_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    water_reminders_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    quiet_start: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
    )
    quiet_end: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notification_preference",
    )
