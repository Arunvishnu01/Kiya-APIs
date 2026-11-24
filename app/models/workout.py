import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    level: Mapped[str] = mapped_column(
        String(30),
        default="BEGINNER",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    sessions: Mapped[List["WorkoutSession"]] = relationship(
        "WorkoutSession",
        back_populates="workout_plan",
        cascade="all, delete-orphan",
        order_by="WorkoutSession.day_number, WorkoutSession.display_order",
    )
    assignments: Mapped[List["WorkoutAssignment"]] = relationship(
        "WorkoutAssignment",
        back_populates="workout_plan",
    )


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    workout_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Relationships
    workout_plan: Mapped["WorkoutPlan"] = relationship(
        "WorkoutPlan",
        back_populates="sessions",
    )
    videos: Mapped[List["WorkoutVideo"]] = relationship(
        "WorkoutVideo",
        back_populates="workout_session",
        cascade="all, delete-orphan",
        order_by="WorkoutVideo.display_order",
    )


class WorkoutVideo(Base):
    __tablename__ = "workout_videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workout_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    min_coverage_pct: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=80.0,
        nullable=False,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    # Relationships
    workout_session: Mapped["WorkoutSession"] = relationship(
        "WorkoutSession",
        back_populates="videos",
    )
    progress_entries: Mapped[List["WorkoutVideoProgress"]] = relationship(
        "WorkoutVideoProgress",
        back_populates="video",
    )


class WorkoutAssignment(Base):
    __tablename__ = "workout_assignments"

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
    workout_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(25),
        default="ACTIVE",
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="workout_assignments",
    )
    workout_plan: Mapped["WorkoutPlan"] = relationship(
        "WorkoutPlan",
        back_populates="assignments",
    )
    video_progresses: Mapped[List["WorkoutVideoProgress"]] = relationship(
        "WorkoutVideoProgress",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class WorkoutVideoProgress(Base):
    __tablename__ = "workout_video_progresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workout_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workout_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    covered_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    eligible_for_completion: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    assignment: Mapped["WorkoutAssignment"] = relationship(
        "WorkoutAssignment",
        back_populates="video_progresses",
    )
    video: Mapped["WorkoutVideo"] = relationship(
        "WorkoutVideo",
        back_populates="progress_entries",
    )
