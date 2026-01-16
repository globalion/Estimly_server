from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserModel(BaseModel):
    full_name: str
    email: EmailStr
    password_hash: str
    role: str
    company_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
