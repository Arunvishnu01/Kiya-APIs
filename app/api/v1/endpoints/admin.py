from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.dependencies import get_admin_user
from app.models.user import User, UserProfile
from app.models.meal import MealSubmission, ScheduledMeal, MealReview, MealTemplateItem
from app.schemas.meal import MealReviewRequest

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin dashboard: pending reviews, action counts."""
    # Count pending reviews
    pending_result = await db.execute(
        select(func.count(MealSubmission.id)).where(
            MealSubmission.status == "PENDING_REVIEW"
        )
    )
    pending_count = int(pending_result.scalar() or 0)

    # Recent pending submissions
    recent_result = await db.execute(
        select(MealSubmission, ScheduledMeal, UserProfile).join(
            ScheduledMeal, MealSubmission.scheduled_meal_id == ScheduledMeal.id
        ).join(
            UserProfile, MealSubmission.user_id == UserProfile.user_id
        ).where(
            MealSubmission.status == "PENDING_REVIEW"
        ).order_by(MealSubmission.submitted_at.desc()).limit(10)
    )
    recent = recent_result.all()

    return {
        "pending_reviews": pending_count,
        "recent_submissions": [
            {
                "id": str(s.id),
                "user_name": p.full_name,
                "submitted_at": s.submitted_at,
                "status": s.status,
            }
            for s, sm, p in recent
        ],
    }


@router.get("/meal-submissions")
async def list_meal_submissions(
    submission_status: str = Query("PENDING_REVIEW", alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin review queue — paginated submissions by status."""
    offset = (page - 1) * limit
    result = await db.execute(
        select(MealSubmission, UserProfile).join(
            UserProfile, MealSubmission.user_id == UserProfile.user_id
        ).where(
            MealSubmission.status == submission_status
        ).order_by(MealSubmission.submitted_at.desc()).limit(limit).offset(offset)
    )
    rows = result.all()
    return {
        "submissions": [
            {
                "id": str(s.id),
                "user_name": p.full_name,
                "user_id": str(s.user_id),
                "status": s.status,
                "revision_no": s.revision_no,
                "submitted_at": s.submitted_at,
            }
            for s, p in rows
        ],
        "page": page,
        "limit": limit,
    }


@router.post("/meal-submissions/{submission_id}/review")
async def review_meal_submission(
    submission_id: str,
    payload: MealReviewRequest,
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or request changes on a meal submission."""
    result = await db.execute(
        select(MealSubmission).where(MealSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if submission.status != "PENDING_REVIEW":
        raise HTTPException(status_code=409, detail=f"Cannot review — status is {submission.status}.")

    # Check no existing review (prevent double review)
    existing_review = await db.execute(
        select(MealReview).where(MealReview.submission_id == submission_id)
    )
    if existing_review.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This submission has already been reviewed.")

    # Create review record
    review = MealReview(
        submission_id=submission_id,
        reviewer_user_id=current_admin.id,
        decision=payload.decision,
        comment=payload.comment,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(review)

    # Update submission status
    if payload.decision == "APPROVED":
        submission.status = "COMPLETED"
        submission.completed_at = datetime.now(timezone.utc)
        # Update scheduled meal
        meal_result = await db.execute(
            select(ScheduledMeal).where(ScheduledMeal.id == submission.scheduled_meal_id)
        )
        meal = meal_result.scalar_one_or_none()
        if meal:
            meal.status = "COMPLETED"
    else:
        submission.status = "CHANGES_REQUESTED"
        meal_result = await db.execute(
            select(ScheduledMeal).where(ScheduledMeal.id == submission.scheduled_meal_id)
        )
        meal = meal_result.scalar_one_or_none()
        if meal:
            meal.status = "CHANGES_REQUESTED"

    await db.commit()
    return {
        "message": f"Submission {payload.decision.lower()}.",
        "new_status": submission.status,
    }


@router.get("/users")
async def list_users(
    search: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=50),
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Search and list users (non-admin users)."""
    from app.models.user import User as UserModel
    offset = (page - 1) * limit
    query = select(UserModel, UserProfile).join(
        UserProfile, UserModel.id == UserProfile.user_id
    ).where(
        UserModel.role == "USER",
        UserModel.deleted_at.is_(None),
    )
    if search:
        query = query.where(UserProfile.full_name.ilike(f"%{search}%"))

    result = await db.execute(query.limit(limit).offset(offset))
    rows = result.all()
    return {
        "users": [
            {
                "id": str(u.id),
                "name": p.full_name,
                "email": u.email,
                "phone": u.phone_e164,
                "status": u.status,
                "onboarding_completed": p.onboarding_completed_at is not None,
            }
            for u, p in rows
        ]
    }
