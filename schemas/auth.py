from pydantic import BaseModel, EmailStr

class SignupRequest(BaseModel):
    full_name: str
    company_name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    role: str
    company_id: str
