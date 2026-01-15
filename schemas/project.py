from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    client_name: str
    description: Optional[str]

    estimation_technique: str
    target_margin: float
    risk_buffer: float
    negotiation_buffer: float
    estimated_team_size: int


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    estimation_technique: Optional[str] = None
    target_margin: Optional[float] = None
    risk_buffer: Optional[float] = None
    negotiation_buffer: Optional[float] = None
    estimated_team_size: Optional[int] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    client_name: str
    description: Optional[str]

    estimation_technique: str
    target_margin: float
    risk_buffer: float
    negotiation_buffer: float
    estimated_team_size: int

    status: str
    company_id: str
    created_by: str
    created_at: datetime
