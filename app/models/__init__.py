from app.core.database import Base
from app.models.user import (
    NotificationPreference,
    User,
    UserDeviceToken,
    UserGoal,
    UserProfile,
)
from app.models.meal import (
    MealPlanAssignment,
    MealPlanTemplate,
    MealReview,
    MealSubmission,
    MealSubmissionPhoto,
    MealTemplateItem,
    ScheduledMeal,
)
from app.models.workout import (
    WorkoutAssignment,
    WorkoutPlan,
    WorkoutSession,
    WorkoutVideo,
    WorkoutVideoProgress,
)
from app.models.water import WaterGoal, WaterLogEntry
from app.models.progress import WeightLogEntry
from app.models.notification import Notification
from app.models.subscription import PlanEnrollment, SubscriptionPlan

__all__ = [
    "Base",
    "User",
    "UserProfile",
    "UserGoal",
    "UserDeviceToken",
    "NotificationPreference",
    "MealPlanTemplate",
    "MealTemplateItem",
    "MealPlanAssignment",
    "ScheduledMeal",
    "MealSubmission",
    "MealSubmissionPhoto",
    "MealReview",
    "WorkoutPlan",
    "WorkoutSession",
    "WorkoutVideo",
    "WorkoutAssignment",
    "WorkoutVideoProgress",
    "WaterGoal",
    "WaterLogEntry",
    "WeightLogEntry",
    "Notification",
    "SubscriptionPlan",
    "PlanEnrollment",
]
