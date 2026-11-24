from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User, UserProfile, UserGoal, NotificationPreference
from app.schemas.user import (
    UserProfileRequest,
    UserProfileResponse,
    GoalRequest,
    GoalResponse,
    MeResponse,
)

router = APIRouter()


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user info."""
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    return MeResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone_e164=current_user.phone_e164,
        role=current_user.role,
        full_name=profile.full_name if profile else "User",
        onboarding_completed=profile.onboarding_completed_at is not None if profile else False,
        avatar_object_key=profile.avatar_object_key if profile else None,
    )


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_profile(
    payload: UserProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update user profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    profile.full_name = payload.full_name
    profile.date_of_birth = payload.date_of_birth
    profile.height_cm = payload.height_cm
    profile.timezone = payload.timezone or "Asia/Kolkata"
    profile.activity_preference = payload.activity_preference

    # Mark onboarding complete when profile is first saved
    if profile.onboarding_completed_at is None:
        profile.onboarding_completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(profile)

    return UserProfileResponse(
        user_id=str(profile.user_id),
        full_name=profile.full_name,
        date_of_birth=profile.date_of_birth,
        height_cm=float(profile.height_cm) if profile.height_cm else None,
        timezone=profile.timezone,
        activity_preference=profile.activity_preference,
        onboarding_completed=profile.onboarding_completed_at is not None,
    )


@router.get("/me/goals", response_model=list[GoalResponse])
async def get_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's current active goals."""
    result = await db.execute(
        select(UserGoal).where(
            UserGoal.user_id == current_user.id,
            UserGoal.ended_at.is_(None),
        )
    )
    goals = result.scalars().all()
    return [
        GoalResponse(
            id=str(g.id),
            goal_type=g.goal_type,
            is_primary=g.is_primary,
            started_at=g.started_at,
        )
        for g in goals
    ]


@router.put("/me/goals")
async def set_goals(
    payload: list[GoalRequest],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Replace user's goals. Ends previous goals and sets new ones."""
    # End existing active goals
    result = await db.execute(
        select(UserGoal).where(
            UserGoal.user_id == current_user.id,
            UserGoal.ended_at.is_(None),
        )
    )
    existing = result.scalars().all()
    now = datetime.now(timezone.utc)
    for g in existing:
        g.ended_at = now

    # Create new goals
    for item in payload:
        goal = UserGoal(
            user_id=current_user.id,
            goal_type=item.goal_type,
            is_primary=item.is_primary,
            started_at=now,
        )
        db.add(goal)

    await db.commit()
    return {"message": "Goals updated successfully."}


@router.put("/me/notification-preferences")
async def update_notification_preferences(
    push_enabled: bool = True,
    meal_reminders_enabled: bool = True,
    water_reminders_enabled: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update notification preferences."""
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == current_user.id)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        pref = NotificationPreference(user_id=current_user.id)
        db.add(pref)

    pref.push_enabled = push_enabled
    pref.meal_reminders_enabled = meal_reminders_enabled
    pref.water_reminders_enabled = water_reminders_enabled

    await db.commit()
    return {"message": "Notification preferences updated."}
