from pydantic import BaseModel, Field
from typing import Optional


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
