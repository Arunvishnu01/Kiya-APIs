from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.meal import (
    MealPlanAssignment, MealPlanTemplate, MealTemplateItem,
    ScheduledMeal, MealSubmission, MealSubmissionPhoto, MealReview
)
from app.schemas.meal import MealSubmitRequest, MealReviewRequest

router = APIRouter()


@router.get("/meals/today")
async def get_meals_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    # Get active assignment
    assignment_result = await db.execute(
        select(MealPlanAssignment).where(
            MealPlanAssignment.user_id == current_user.id,
            MealPlanAssignment.status == "ACTIVE",
            MealPlanAssignment.start_date <= today,
        ).order_by(MealPlanAssignment.start_date.desc())
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        return {"meals": [], "message": "No meal plan assigned yet."}

    # Get today's scheduled meals
    meals_result = await db.execute(
        select(ScheduledMeal, MealTemplateItem).join(
            MealTemplateItem, ScheduledMeal.meal_template_item_id == MealTemplateItem.id
        ).where(
            ScheduledMeal.assignment_id == assignment.id,
            ScheduledMeal.scheduled_date == today,
        ).order_by(MealTemplateItem.display_order)
    )
    rows = meals_result.all()

    meals_out = []
    for scheduled, item in rows:
        # Get latest submission
        sub_result = await db.execute(
            select(MealSubmission).where(
                MealSubmission.scheduled_meal_id == scheduled.id,
                MealSubmission.user_id == current_user.id,
            ).order_by(MealSubmission.revision_no.desc())
        )
        submission = sub_result.scalar_one_or_none()

        meals_out.append({
            "id": str(scheduled.id),
            "meal_type": item.meal_type,
            "title": item.title,
            "instructions": item.instructions,
            "scheduled_date": scheduled.scheduled_date.isoformat(),
            "status": scheduled.status,
            "submission": {
                "id": str(submission.id),
                "status": submission.status,
                "revision_no": submission.revision_no,
                "submitted_at": submission.submitted_at,
            } if submission else None,
        })

    return {
        "assignment_id": str(assignment.id),
        "day_number": (today - assignment.start_date).days + 1,
        "meals": meals_out,
    }


@router.get("/meals")
async def get_meals_by_date(
    date_str: str = Query(..., alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_date = date.fromisoformat(date_str)
    # Reuse today logic but for target_date
    assignment_result = await db.execute(
        select(MealPlanAssignment).where(
            MealPlanAssignment.user_id == current_user.id,
            MealPlanAssignment.status == "ACTIVE",
            MealPlanAssignment.start_date <= target_date,
        ).order_by(MealPlanAssignment.start_date.desc())
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        return {"meals": []}

    meals_result = await db.execute(
        select(ScheduledMeal, MealTemplateItem).join(
            MealTemplateItem, ScheduledMeal.meal_template_item_id == MealTemplateItem.id
        ).where(
            ScheduledMeal.assignment_id == assignment.id,
            ScheduledMeal.scheduled_date == target_date,
        )
    )
    rows = meals_result.all()
    return {
        "meals": [
            {"id": str(s.id), "meal_type": item.meal_type, "title": item.title, "status": s.status}
            for s, item in rows
        ]
    }


@router.post("/meals/{scheduled_meal_id}/submissions", status_code=status.HTTP_201_CREATED)
async def create_or_get_submission(
    scheduled_meal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get existing DRAFT or create a new draft submission."""
    # Verify ownership
    meal_result = await db.execute(
        select(ScheduledMeal).where(ScheduledMeal.id == scheduled_meal_id)
    )
    scheduled_meal = meal_result.scalar_one_or_none()
    if not scheduled_meal:
        raise HTTPException(status_code=404, detail="Scheduled meal not found.")

    # Check existing draft
    existing = await db.execute(
        select(MealSubmission).where(
            MealSubmission.scheduled_meal_id == scheduled_meal_id,
            MealSubmission.user_id == current_user.id,
            MealSubmission.status == "DRAFT",
        )
    )
    submission = existing.scalar_one_or_none()
    if submission:
        return {"id": str(submission.id), "status": submission.status, "revision_no": submission.revision_no}

    # Get latest revision number
    rev_result = await db.execute(
        select(MealSubmission).where(
            MealSubmission.scheduled_meal_id == scheduled_meal_id,
        ).order_by(MealSubmission.revision_no.desc())
    )
    latest = rev_result.scalar_one_or_none()
    next_rev = (latest.revision_no + 1) if latest else 1

    new_submission = MealSubmission(
        scheduled_meal_id=scheduled_meal_id,
        user_id=current_user.id,
        revision_no=next_rev,
        status="DRAFT",
    )
    db.add(new_submission)
    await db.commit()
    await db.refresh(new_submission)
    return {"id": str(new_submission.id), "status": "DRAFT", "revision_no": next_rev}


@router.post("/meal-submissions/{submission_id}/submit")
async def submit_for_review(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a draft submission as PENDING_REVIEW."""
    result = await db.execute(
        select(MealSubmission).where(
            MealSubmission.id == submission_id,
            MealSubmission.user_id == current_user.id,
        )
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if submission.status != "DRAFT":
        raise HTTPException(status_code=409, detail=f"Cannot submit — current status is {submission.status}.")

    submission.status = "PENDING_REVIEW"
    submission.submitted_at = datetime.now(timezone.utc)

    # Update scheduled meal status
    meal_result = await db.execute(
        select(ScheduledMeal).where(ScheduledMeal.id == submission.scheduled_meal_id)
    )
    meal = meal_result.scalar_one_or_none()
    if meal:
        meal.status = "PENDING_REVIEW"

    await db.commit()
    return {"message": "Submitted for review.", "status": "PENDING_REVIEW"}
