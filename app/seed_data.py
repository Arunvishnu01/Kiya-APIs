"""
Seed data script — run once to populate subscription plans.
Usage: python -m app.seed_data
"""
import asyncio
from decimal import Decimal
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.subscription import SubscriptionPlan


PLANS = [
    {
        "code": "MONTHLY",
        "name": "Monthly",
        "period_days": 30,
        "price": Decimal("1499.00"),
        "currency": "INR",
        "features": ["Personalised meal plan", "Workout plan", "Coach support"],
        "is_active": True,
    },
    {
        "code": "QUARTERLY",
        "name": "3 Months",
        "period_days": 90,
        "price": Decimal("3999.00"),
        "currency": "INR",
        "features": ["Personalised meal plan", "Workout plan", "Coach support", "Save 11%"],
        "is_active": True,
    },
    {
        "code": "YEARLY",
        "name": "Yearly",
        "period_days": 365,
        "price": Decimal("11999.00"),
        "currency": "INR",
        "features": ["Personalised meal plan", "Workout plan", "Coach support", "Save 33%"],
        "is_active": True,
    },
]


async def seed():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        from sqlalchemy import select
        for plan_data in PLANS:
            result = await session.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.code == plan_data["code"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                plan = SubscriptionPlan(**plan_data)
                session.add(plan)
                print(f"✅ Created plan: {plan_data['name']} — ₹{plan_data['price']}")
            else:
                print(f"⏭️  Plan already exists: {plan_data['name']}")
        await session.commit()
    print("\n🌱 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
