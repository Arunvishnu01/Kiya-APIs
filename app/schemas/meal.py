import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MealPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_key: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime


class MealReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    decision: str
    comment: Optional[str] = None
    reviewed_at: datetime
    reviewer_user_id: Optional[uuid.UUID] = None


class MealSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scheduled_meal_id: uuid.UUID
    status: str
    revision_no: int
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    photos_count: int = 0
    photos: List[MealPhotoResponse] = []
    review: Optional[MealReviewResponse] = None


class ScheduledMealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    meal_type: str
    title: str
    instructions: Optional[str] = None
    scheduled_date: date
    status: str
    submission: Optional[MealSubmissionResponse] = None


class MealSubmitRequest(BaseModel):
    pass


class MealReviewRequest(BaseModel):
    decision: str = Field(pattern="^(APPROVED|CHANGES_REQUESTED)$")
    comment: Optional[str] = None


class MealPhotoCreate(BaseModel):
    object_key: str
    content_type: str
    size_bytes: int


class MealSubmissionCreateRequest(BaseModel):
    photos: List[MealPhotoCreate] = []
