from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.subscription import SubscriptionPlan, PlanEnrollment

router = APIRouter()


@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    """List all active subscription plans — public endpoint."""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
        .order_by(SubscriptionPlan.period_days)
    )
    plans = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "code": p.code,
            "name": p.name,
            "period_days": p.period_days,
            "price": float(p.price),
            "currency": p.currency,
            "features": p.features or [],
            "is_active": p.is_active,
        }
        for p in plans
    ]


@router.get("/me/enrollment")
async def get_my_enrollment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlanEnrollment, SubscriptionPlan).join(
            SubscriptionPlan, PlanEnrollment.subscription_plan_id == SubscriptionPlan.id
        ).where(
            PlanEnrollment.user_id == current_user.id,
            PlanEnrollment.status.in_(["ACTIVE", "TRIAL"]),
        ).order_by(PlanEnrollment.starts_at.desc())
    )
    row = result.first()
    if not row:
        return {"enrollment": None}
    enrollment, plan = row
    return {
        "enrollment": {
            "id": str(enrollment.id),
            "status": enrollment.status,
            "starts_at": enrollment.starts_at,
            "ends_at": enrollment.ends_at,
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "period_days": plan.period_days,
                "price": float(plan.price),
                "currency": plan.currency,
            },
        }
    }
