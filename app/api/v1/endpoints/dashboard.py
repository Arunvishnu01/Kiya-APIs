from typing import Optional
from datetime import datetime, timezone, date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_user
from app.models.user import User, UserProfile, UserGoal
from app.models.meal import MealPlanAssignment, ScheduledMeal, MealSubmission
from app.models.water import WaterLogEntry, WaterGoal
from app.models.workout import WorkoutAssignment, WorkoutSession, WorkoutVideoProgress
from app.models.notification import Notification
from app.models.subscription import PlanEnrollment, SubscriptionPlan
from app.schemas.dashboard import DashboardResponse, MealsSummary, WaterSummary, WorkoutSummary

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    date_str: Optional[str] = Query(None, alias="date", description="YYYY-MM-DD, defaults to today"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate dashboard data for the user's local day."""
    today = date.fromisoformat(date_str) if date_str else date.today()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)

    # User profile
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    display_name = profile.full_name.split()[0] if profile else "Friend"

    # Active goal
    goal_result = await db.execute(
        select(UserGoal).where(
            UserGoal.user_id == current_user.id,
            UserGoal.is_primary == True,
            UserGoal.ended_at.is_(None),
        )
    )
    goal = goal_result.scalar_one_or_none()
    goal_type = goal.goal_type if goal else "GENERAL_WELLNESS"

    # Meals summary
    meals_result = await db.execute(
        select(ScheduledMeal).where(
            ScheduledMeal.scheduled_date == today,
            ScheduledMeal.assignment_id.in_(
                select(MealPlanAssignment.id).where(
                    MealPlanAssignment.user_id == current_user.id,
                    MealPlanAssignment.status == "ACTIVE",
                )
            ),
        )
    )
    scheduled_meals = meals_result.scalars().all()
    scheduled_count = len(scheduled_meals)
    submitted_count = sum(1 for m in scheduled_meals if m.status in ("PENDING_REVIEW", "COMPLETED"))
    completed_count = sum(1 for m in scheduled_meals if m.status == "COMPLETED")

    # Water summary
    water_goal_result = await db.execute(
        select(WaterGoal).where(WaterGoal.user_id == current_user.id).order_by(WaterGoal.effective_from.desc())
    )
    water_goal = water_goal_result.scalar_one_or_none()
    daily_target_ml = water_goal.daily_target_ml if water_goal else 1000
    checkpoint_ml = water_goal.checkpoint_ml if water_goal else 250

    water_log_result = await db.execute(
        select(func.coalesce(func.sum(WaterLogEntry.quantity_ml), 0)).where(
            WaterLogEntry.user_id == current_user.id,
            WaterLogEntry.consumed_at >= today_start,
            WaterLogEntry.consumed_at < today_end,
        )
    )
    logged_ml = int(water_log_result.scalar() or 0)

    # Next checkpoint
    next_checkpoint = checkpoint_ml
    while next_checkpoint <= logged_ml and next_checkpoint < daily_target_ml:
        next_checkpoint += checkpoint_ml

    # Workout summary
    workout_name = None
    videos_completed = 0
    videos_total = 0
    workout_assign_result = await db.execute(
        select(WorkoutAssignment).where(
            WorkoutAssignment.user_id == current_user.id,
            WorkoutAssignment.status == "ACTIVE",
        ).order_by(WorkoutAssignment.start_date.desc())
    )
    workout_assignment = workout_assign_result.scalar_one_or_none()
    if workout_assignment:
        day_num = (today - workout_assignment.start_date).days + 1
        session_result = await db.execute(
            select(WorkoutSession).where(
                WorkoutSession.workout_plan_id == workout_assignment.workout_plan_id,
                WorkoutSession.day_number == day_num,
            )
        )
        session = session_result.scalar_one_or_none()
        if session:
            workout_name = session.title
            progress_result = await db.execute(
                select(WorkoutVideoProgress).where(
                    WorkoutVideoProgress.assignment_id == workout_assignment.id,
                )
            )
            progress_records = progress_result.scalars().all()
            videos_total = len(progress_records)
            videos_completed = sum(1 for p in progress_records if p.eligible_for_completion)

    # Unread notifications
    notif_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    )
    unread_count = int(notif_result.scalar() or 0)

    # Selected plan
    enrollment_result = await db.execute(
        select(PlanEnrollment, SubscriptionPlan).join(
            SubscriptionPlan, PlanEnrollment.subscription_plan_id == SubscriptionPlan.id
        ).where(
            PlanEnrollment.user_id == current_user.id,
            PlanEnrollment.status.in_(["ACTIVE", "TRIAL"]),
        ).order_by(PlanEnrollment.starts_at.desc())
    )
    enrollment_row = enrollment_result.first()
    selected_plan = None
    if enrollment_row:
        _, plan = enrollment_row
        selected_plan = {"id": str(plan.id), "name": plan.name}

    # WhatsApp URL
    plan_name = selected_plan["name"] if selected_plan else "Wellness Plan"
    whatsapp_message = (
        f"Hello Healthy Growth with Kiya team,\n"
        f"I would like details about my selected wellness plan.\n"
        f"Plan: {plan_name}\n"
        f"Preferred name: {display_name}\n"
        f"Please share the next steps."
    )
    import urllib.parse
    whatsapp_url = f"https://wa.me/{settings.WHATSAPP_BUSINESS_PHONE}?text={urllib.parse.quote(whatsapp_message)}"

    return DashboardResponse(
        date=today.isoformat(),
        display_name=display_name,
        goal=goal_type,
        selected_plan=selected_plan,
        meals=MealsSummary(
            scheduled=scheduled_count,
            submitted=submitted_count,
            completed=completed_count,
        ),
        water=WaterSummary(
            logged_ml=logged_ml,
            goal_ml=daily_target_ml,
            next_checkpoint_ml=min(next_checkpoint, daily_target_ml),
        ),
        workout=WorkoutSummary(
            session_name=workout_name,
            required_videos_completed=videos_completed,
            required_videos_total=videos_total,
        ),
        notifications_unread=unread_count,
        whatsapp_url=whatsapp_url,
    )
