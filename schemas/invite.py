from pydantic import BaseModel, EmailStr

class InviteRequest(BaseModel):
    email: EmailStr
    role: str

class AcceptInviteRequest(BaseModel):
    token: str
    full_name: str
    password: str


