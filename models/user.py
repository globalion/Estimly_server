from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    full_name: str
    email: EmailStr
    password_hash: str
    role: str = "ADMIN"     # first user = ADMIN
    company_id: str

    class Config:
        populate_by_name = True
