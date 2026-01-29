from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EstimationTechnique(BaseModel):
    key: str
    code: str
    created_at: Optional[datetime] = None


class EstimationTechniqueInfo(BaseModel):
    technique_key: str
    name: str
    standard: str
    description: str
    use_cases: str
    complexity: str
    time_required: str
    accuracy: str


class EstimationSettings(BaseModel):
    default_margin_percent: int
    default_risk_buffer: int
    default_negotiation_buffer: int
    productivity_factor: float
    sprint_duration_weeks: int
    working_hours_per_day: int
    working_days_per_week: int
    default_estimation_technique: str