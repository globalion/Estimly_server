from pydantic import BaseModel, Field
from typing import List, Optional

class TaskSchema(BaseModel):
    name: str
    hours: int = Field(gt=0)  
    role: str
    level: str

class FeatureSchema(BaseModel):
    name: str
    tasks: List[TaskSchema]

class ModuleSchema(BaseModel):
    name: str
    features: List[FeatureSchema]

class CustomTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    default_margin: float
    default_risk_buffer: float
    modules: List[ModuleSchema]

class CustomTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_margin: Optional[float] = None
    default_risk_buffer: Optional[float] = None
    modules: Optional[List[ModuleSchema]] = None