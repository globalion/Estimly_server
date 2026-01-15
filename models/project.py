from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Project(BaseModel):
    name: str
    client_name: str
    description: Optional[str] = None

    estimation_technique: str
    target_margin: float
    risk_buffer: float
    negotiation_buffer: float
    estimated_team_size: int

    status: str = "DRAFT"

    company_id: str
    created_by: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
