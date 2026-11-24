import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
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


class MealPlanTemplate(Base):
    __tablename__ = "meal_plan_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
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
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    items: Mapped[List["MealTemplateItem"]] = relationship(
        "MealTemplateItem",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="MealTemplateItem.day_number, MealTemplateItem.display_order",
    )
    assignments: Mapped[List["MealPlanAssignment"]] = relationship(
        "MealPlanAssignment",
        back_populates="template",
    )


class MealTemplateItem(Base):
    __tablename__ = "meal_template_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_plan_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_number: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    meal_type: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        nullable=False,
    )

    # Relationships
    template: Mapped["MealPlanTemplate"] = relationship(
        "MealPlanTemplate",
        back_populates="items",
    )
    scheduled_meals: Mapped[List["ScheduledMeal"]] = relationship(
        "ScheduledMeal",
        back_populates="template_item",
    )


class MealPlanAssignment(Base):
    __tablename__ = "meal_plan_assignments"

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
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_plan_templates.id", ondelete="CASCADE"),
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
        back_populates="meal_assignments",
    )
    template: Mapped["MealPlanTemplate"] = relationship(
        "MealPlanTemplate",
        back_populates="assignments",
    )
    scheduled_meals: Mapped[List["ScheduledMeal"]] = relationship(
        "ScheduledMeal",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class ScheduledMeal(Base):
    __tablename__ = "scheduled_meals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_plan_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meal_template_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_template_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(25),
        default="NOT_SUBMITTED",
        nullable=False,
    )

    # Relationships
    assignment: Mapped["MealPlanAssignment"] = relationship(
        "MealPlanAssignment",
        back_populates="scheduled_meals",
    )
    template_item: Mapped["MealTemplateItem"] = relationship(
        "MealTemplateItem",
        back_populates="scheduled_meals",
        lazy="selectin",
    )
    submissions: Mapped[List["MealSubmission"]] = relationship(
        "MealSubmission",
        back_populates="scheduled_meal",
        cascade="all, delete-orphan",
        order_by="MealSubmission.revision_no.desc()",
        lazy="selectin",
    )


class MealSubmission(Base):
    __tablename__ = "meal_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scheduled_meal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_meals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    revision_no: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(25),
        default="DRAFT",
        nullable=False,
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'PENDING_REVIEW', 'COMPLETED', 'CHANGES_REQUESTED')",
            name="check_meal_submission_status",
        ),
    )

    # Relationships
    scheduled_meal: Mapped["ScheduledMeal"] = relationship(
        "ScheduledMeal",
        back_populates="submissions",
    )
    user: Mapped["User"] = relationship(
        "User",
    )
    photos: Mapped[List["MealSubmissionPhoto"]] = relationship(
        "MealSubmissionPhoto",
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    review: Mapped[Optional["MealReview"]] = relationship(
        "MealReview",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MealSubmissionPhoto(Base):
    __tablename__ = "meal_submission_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    object_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    submission: Mapped["MealSubmission"] = relationship(
        "MealSubmission",
        back_populates="photos",
    )


class MealReview(Base):
    __tablename__ = "meal_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meal_submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    reviewer_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "decision IN ('APPROVED', 'CHANGES_REQUESTED')",
            name="check_meal_review_decision",
        ),
    )

    # Relationships
    submission: Mapped["MealSubmission"] = relationship(
        "MealSubmission",
        back_populates="review",
    )
    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
    )
