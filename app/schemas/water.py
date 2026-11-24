import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WaterLogRequest(BaseModel):
    quantity_ml: int = Field(gt=0, le=2000, description="Amount of water in ml (1-2000)")
    consumed_at: datetime
    client_request_id: uuid.UUID


class WaterLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quantity_ml: int
    consumed_at: datetime
    client_request_id: uuid.UUID
    created_at: datetime


class WaterGoalRequest(BaseModel):
    daily_target_ml: int = Field(ge=500, le=10000, default=1000)
    checkpoint_ml: Optional[int] = Field(default=250, ge=100, le=1000)


class WaterLogEntryResponse(BaseModel):
    id: str
    quantity_ml: int
    consumed_at: datetime


class WaterTodayResponse(BaseModel):
    logged_ml: int
    goal_ml: int
    next_checkpoint_ml: int
    entries: list[WaterLogEntryResponse] = []
