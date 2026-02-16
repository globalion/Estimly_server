from fastapi import APIRouter, Depends
from utils.auth_jwt import get_current_user
from schemas.invitation import CreateInvitationRequest
from services.invitation_service import create_invitation_service


router = APIRouter(prefix="/invitation", tags=["Invitation"])


@router.post("/create")
async def create_invitation(
    payload: CreateInvitationRequest,
    current_user=Depends(get_current_user)
):
    invitation = await create_invitation_service(
        user_id=str(current_user["_id"]),
        expires_in_hours=payload.expires_in_hours,
        max_uses=payload.max_uses,
        invite_type=payload.invite_type
    )

    return {
        "message": "Invitation created successfully",
        "invite_link": f"http://localhost:3000/register?invite={invitation['invite_code']}",
        "expires_at": invitation["expires_at"],
        "max_uses": invitation["max_uses"],
        "invite_type": invitation["invite_type"]
    }
