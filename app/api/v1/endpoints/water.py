from datetime import datetime, timezone, date, timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.water import WaterLogEntry, WaterGoal
from app.schemas.water import WaterLogRequest, WaterTodayResponse, WaterLogEntryResponse

router = APIRouter()


@router.get("/today", response_model=WaterTodayResponse)
async def get_water_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)

    # Get goal
    goal_result = await db.execute(
        select(WaterGoal).where(WaterGoal.user_id == current_user.id)
        .order_by(WaterGoal.effective_from.desc())
    )
    goal = goal_result.scalar_one_or_none()
    daily_target_ml = goal.daily_target_ml if goal else 1000
    checkpoint_ml = goal.checkpoint_ml if goal else 250

    # Get today's logs
    logs_result = await db.execute(
        select(WaterLogEntry).where(
            WaterLogEntry.user_id == current_user.id,
            WaterLogEntry.consumed_at >= today_start,
            WaterLogEntry.consumed_at < today_end,
        ).order_by(WaterLogEntry.consumed_at)
    )
    logs = logs_result.scalars().all()
    logged_ml = sum(e.quantity_ml for e in logs)

    # Next checkpoint
    next_checkpoint = checkpoint_ml
    while next_checkpoint <= logged_ml and next_checkpoint < daily_target_ml:
        next_checkpoint += checkpoint_ml

    return WaterTodayResponse(
        logged_ml=logged_ml,
        goal_ml=daily_target_ml,
        next_checkpoint_ml=min(next_checkpoint, daily_target_ml),
        entries=[
            WaterLogEntryResponse(
                id=str(e.id),
                quantity_ml=e.quantity_ml,
                consumed_at=e.consumed_at,
            )
            for e in logs
        ],
    )


@router.post("/logs", status_code=status.HTTP_201_CREATED)
async def add_water_log(
    payload: WaterLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a water log entry. Idempotent via client_request_id."""
    # Check idempotency
    existing = await db.execute(
        select(WaterLogEntry).where(
            WaterLogEntry.user_id == current_user.id,
            WaterLogEntry.client_request_id == payload.client_request_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"message": "Entry already recorded.", "idempotent": True}

    entry = WaterLogEntry(
        user_id=current_user.id,
        quantity_ml=payload.quantity_ml,
        consumed_at=payload.consumed_at,
        client_request_id=payload.client_request_id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return {"id": str(entry.id), "quantity_ml": entry.quantity_ml, "message": "Water logged!"}


@router.delete("/logs/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_water_log(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WaterLogEntry).where(
            WaterLogEntry.id == entry_id,
            WaterLogEntry.user_id == current_user.id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found.")
    await db.delete(entry)
    await db.commit()


@router.put("/goal")
async def update_water_goal(
    daily_target_ml: int = 1000,
    checkpoint_ml: int = 250,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if daily_target_ml <= 0 or checkpoint_ml <= 0:
        raise HTTPException(status_code=400, detail="Values must be positive.")

    goal = WaterGoal(
        user_id=current_user.id,
        daily_target_ml=daily_target_ml,
        checkpoint_ml=checkpoint_ml,
        effective_from=date.today(),
    )
    db.add(goal)
    await db.commit()
    return {"message": "Water goal updated.", "daily_target_ml": daily_target_ml}
