from pydantic import BaseModel, Field
from typing import Optional

class ResourceRoleCreate(BaseModel):
    label: str
    hourly_rate: float = Field(gt=0)


class ResourceRoleUpdate(BaseModel):
    label: Optional[str] = Field(None)
    hourly_rate: Optional[float] = Field(None, gt=0)

