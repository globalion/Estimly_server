from pydantic import BaseModel
from typing import List, Optional


class Addon(BaseModel):
    name: str
    extra_hours: int


class BuiltInTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    modules: List[str] = []
    addons: List[Addon] = []
    default_margin: int
    risk_buffer: int


class BuiltInTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    modules: Optional[List[str]] = None
    addons: Optional[List[Addon]] = None
    default_margin: Optional[int] = None
    risk_buffer: Optional[int] = None
