from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class WeightLogRequest(BaseModel):
    weight_kg: float
    measured_on: date


class WeightLogResponse(BaseModel):
    id: str
    weight_kg: float
    measured_on: date
    recorded_at: datetime

    model_config = {"from_attributes": True}


class ProgressSummaryResponse(BaseModel):
    current_weight: Optional[float] = None
    start_weight: Optional[float] = None
    change: Optional[float] = None
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    entries: list[WeightLogResponse] = []
