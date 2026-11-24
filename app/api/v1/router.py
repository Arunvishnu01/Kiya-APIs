from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    profiles,
    dashboard,
    meals,
    water,
    progress,
    notifications,
    plans,
    workouts,
    admin,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profiles.router, tags=["Profile"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(meals.router, tags=["Meals"])
api_router.include_router(workouts.router, tags=["Workouts"])
api_router.include_router(water.router, prefix="/water", tags=["Water"])
api_router.include_router(progress.router, prefix="/progress", tags=["Progress"])
api_router.include_router(notifications.router, tags=["Notifications"])
api_router.include_router(plans.router, tags=["Plans"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
