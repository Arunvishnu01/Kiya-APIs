from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User, UserProfile
from app.models.progress import WeightLogEntry
from app.schemas.progress import WeightLogRequest, WeightLogResponse, ProgressSummaryResponse

router = APIRouter()


def calculate_adult_bmi(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive")
    height_m = height_cm / Decimal("100")
    bmi = weight_kg / (height_m * height_m)
    return bmi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    return "Obese"


@router.get("/weight", response_model=list[WeightLogResponse])
async def get_weight_history(
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(WeightLogEntry).where(WeightLogEntry.user_id == current_user.id)
    if start:
        query = query.where(WeightLogEntry.measured_on >= date.fromisoformat(start))
    if end:
        query = query.where(WeightLogEntry.measured_on <= date.fromisoformat(end))
    query = query.order_by(WeightLogEntry.measured_on)

    result = await db.execute(query)
    entries = result.scalars().all()
    return [
        WeightLogResponse(
            id=str(e.id),
            weight_kg=float(e.weight_kg),
            measured_on=e.measured_on,
            recorded_at=e.recorded_at,
        )
        for e in entries
    ]


@router.post("/weight", response_model=WeightLogResponse, status_code=201)
async def add_weight_entry(
    payload: WeightLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = WeightLogEntry(
        user_id=current_user.id,
        weight_kg=Decimal(str(payload.weight_kg)),
        measured_on=payload.measured_on,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return WeightLogResponse(
        id=str(entry.id),
        weight_kg=float(entry.weight_kg),
        measured_on=entry.measured_on,
        recorded_at=entry.recorded_at,
    )


@router.get("/summary", response_model=ProgressSummaryResponse)
async def get_progress_summary(
    period: str = Query("month", description="week | month | 3months"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    days_map = {"week": 7, "month": 30, "3months": 90}
    days = days_map.get(period, 30)
    start_date = date.today() - timedelta(days=days)

    result = await db.execute(
        select(WeightLogEntry).where(
            WeightLogEntry.user_id == current_user.id,
            WeightLogEntry.measured_on >= start_date,
        ).order_by(WeightLogEntry.measured_on)
    )
    entries = result.scalars().all()

    current_weight = float(entries[-1].weight_kg) if entries else None
    start_weight = float(entries[0].weight_kg) if entries else None
    change = round(current_weight - start_weight, 2) if (current_weight and start_weight) else None

    # BMI only for adults (age >= 20) with height on file
    bmi = None
    bmi_category = None
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile and profile.height_cm and current_weight and profile.date_of_birth:
        from datetime import date as ddate
        age = (ddate.today() - profile.date_of_birth).days // 365
        if age >= 20:
            bmi_val = calculate_adult_bmi(
                Decimal(str(current_weight)), Decimal(str(profile.height_cm))
            )
            bmi = float(bmi_val)
            bmi_category = get_bmi_category(bmi)

    return ProgressSummaryResponse(
        current_weight=current_weight,
        start_weight=start_weight,
        change=change,
        bmi=bmi,
        bmi_category=bmi_category,
        entries=[
            WeightLogResponse(
                id=str(e.id),
                weight_kg=float(e.weight_kg),
                measured_on=e.measured_on,
                recorded_at=e.recorded_at,
            )
            for e in entries
        ],
    )
