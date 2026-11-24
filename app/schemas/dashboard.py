from datetime import date
from typing import Optional
from pydantic import BaseModel


class MealsSummary(BaseModel):
    scheduled: int = 0
    submitted: int = 0
    completed: int = 0


class WaterSummary(BaseModel):
    logged_ml: int = 0
    goal_ml: int = 1000
    next_checkpoint_ml: int = 250
    percentage: float = 0.0


class WorkoutSummary(BaseModel):
    session_name: Optional[str] = None
    required_videos_completed: int = 0
    required_videos_total: int = 0
    is_completed: bool = False


class DashboardResponse(BaseModel):
    date: date
    display_name: str
    goal: Optional[str] = None
    meals: MealsSummary
    water: WaterSummary
    workout: WorkoutSummary
    notifications_unread: int = 0
    plan_name: Optional[str] = None
    whatsapp_url: Optional[str] = None
