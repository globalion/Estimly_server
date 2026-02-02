from pydantic import BaseModel, Field
from typing import List, Optional

class ProjectTaskSchema(BaseModel):
    name: str
    hours: int = Field(gt=0)
    role: str
    level: str


class ProjectFeatureSchema(BaseModel):
    name: str
    tasks: List[ProjectTaskSchema]


class ProjectModuleSchema(BaseModel):
    name: str
    features: List[ProjectFeatureSchema]

class EstimationTechniqueSnapshot(BaseModel):
    name: str
    standard: Optional[str] = None
    description: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str
    client_name: str
    description: Optional[str] = None
    estimation_technique: EstimationTechniqueSnapshot
    target_margin: float
    risk_buffer: float
    negotiation_buffer: float
    estimated_team_size: int

    #  template_id: Optional[str] = None
    template_name: Optional[str] = None
    # template_type: Optional[str] = None 
    
    modules: List[ProjectModuleSchema]


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    estimation_technique: Optional[EstimationTechniqueSnapshot] = None
    target_margin: Optional[float] = None
    risk_buffer: Optional[float] = None
    negotiation_buffer: Optional[float] = None
    estimated_team_size: Optional[int] = None
    status: Optional[str] = None
    modules: Optional[List[ProjectModuleSchema]] = None


class EstimationProjectRequest(BaseModel):
    target_margin: int
    risk_buffer: int
    negotiation_buffer: int
    estimated_team_size: int
    modules: List[ProjectModuleSchema]
