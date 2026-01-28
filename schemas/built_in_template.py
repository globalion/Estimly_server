from pydantic import BaseModel, Field
from typing import List, Optional


class BuiltInTaskSchema(BaseModel):
    name: str
    hours: int = Field(gt=0)
    role: str
    level: str


class BuiltInFeatureSchema(BaseModel):
    name: str
    tasks: List[BuiltInTaskSchema]


class BuiltInModuleSchema(BaseModel):
    name: str
    features: List[BuiltInFeatureSchema]


class BuiltInAddOnSchema(BaseModel):
    name: str
    hours: int = Field(ge=0)
    cost: int = Field(ge=0)


class BuiltInTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    default_margin: float
    default_risk_buffer: float
    modules: List[BuiltInModuleSchema]
    add_ons: List[BuiltInAddOnSchema]


class BuiltInTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_margin: Optional[float] = None
    default_risk_buffer: Optional[float] = None
    modules: Optional[List[BuiltInModuleSchema]] = None
    add_ons: Optional[List[BuiltInAddOnSchema]] = None
    status: Optional[str] = None
