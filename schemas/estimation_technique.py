from pydantic import BaseModel
from typing import List, Optional

class EstimationTechniqueCreate(BaseModel):
    name: str
    standard: str
    description: Optional[str] = None
    best_for: List[str]
    complexity: str
    accuracy: str


class EstimationTechniqueUpdate(BaseModel):
    name: Optional[str] = None
    standard: Optional[str] = None
    description: Optional[str] = None
    best_for: Optional[List[str]] = None
    complexity: Optional[str] = None
    accuracy: Optional[str] = None
    status: Optional[str] = None
