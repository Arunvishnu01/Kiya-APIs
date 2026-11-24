import uuid
from datetime import date, datetime, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    date_of_birth: Optional[date] = None
    height_cm: Optional[float] = Field(default=None, gt=0, lt=300)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    activity_preference: Optional[str] = Field(default=None, max_length=30)
    avatar_object_key: Optional[str] = None


class MeResponse(BaseModel):
    id: str
    email: Optional[str] = None
    phone_e164: Optional[str] = None
    role: str
    full_name: str
    onboarding_completed: bool = False
    avatar_object_key: Optional[str] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str
    date_of_birth: Optional[date] = None
    height_cm: Optional[float] = None
    timezone: str
    activity_preference: Optional[str] = None
    onboarding_completed: bool = False


class GoalRequest(BaseModel):
    goal_type: str = Field(min_length=2, max_length=40)
    is_primary: bool = False


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_type: str
    is_primary: bool
    started_at: datetime
    ended_at: Optional[datetime] = None


class NotificationPreferenceRequest(BaseModel):
    push_enabled: Optional[bool] = None
    meal_reminders_enabled: Optional[bool] = None
    water_reminders_enabled: Optional[bool] = None
    quiet_start: Optional[time] = None
    quiet_end: Optional[time] = None


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    push_enabled: bool
    meal_reminders_enabled: bool
    water_reminders_enabled: bool
    quiet_start: Optional[time] = None
    quiet_end: Optional[time] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: Optional[EmailStr] = None
    phone_e164: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    profile: Optional[UserProfileResponse] = None
