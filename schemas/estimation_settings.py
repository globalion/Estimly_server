from pydantic import BaseModel, Field
from typing import Optional


class EstimationSettingsUpdate(BaseModel):
    productivity_factor: Optional[float] = Field(None, gt=0, lt=1)
    sprint_duration_weeks: Optional[int] = Field(None, gt=0)