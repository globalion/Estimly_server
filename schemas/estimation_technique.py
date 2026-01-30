from pydantic import BaseModel
from typing import Optional, List


class EstimationTechniqueCreate(BaseModel):
    name: str
    standard: str
    description: Optional[str] = None
    use_cases: List[str]
    complexity: str
    time_required: str
    accuracy: str


class EstimationTechniqueUpdate(BaseModel):
    name: Optional[str] = None
    standard: Optional[str] = None
    description: Optional[str] = None
    use_cases: Optional[List[str]] = None
    complexity: Optional[str] = None
    time_required: Optional[str] = None
    accuracy: Optional[str] = None
    status: Optional[str] = None
