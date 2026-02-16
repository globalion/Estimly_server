from pydantic import BaseModel
from typing import Optional


class CreateInvitationRequest(BaseModel):
    expires_in_hours: Optional[int] = 24
    max_uses: Optional[int] = 1
    invite_type: Optional[str] = "company"  # company / user / admin

