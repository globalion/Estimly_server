from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Dict


class SignupRequest(BaseModel):
    full_name: str
    company_name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_new_password: str

    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, confirm_new_password, info):
        if confirm_new_password != info.data.get("new_password"):
            raise ValueError("Passwords do not match")
        return confirm_new_password

class UserResponse(BaseModel):
    email: str
    name: Optional[str]
    auth_type: Optional[str] = "password"
    social_accounts: Optional[Dict[str, str]] = {}
