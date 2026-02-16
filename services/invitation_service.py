import secrets
from datetime import datetime, timedelta
from bson import ObjectId
from database.mongo import invitations_collection


def generate_invite_code():
    return secrets.token_urlsafe(20)


async def create_invitation_service(
    user_id: str,
    expires_in_hours: int,
    max_uses: int,
    invite_type: str
):
    invite_code = generate_invite_code()

    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

    invitation_doc = {
        "invite_code": invite_code,
        "created_by": ObjectId(user_id),
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "max_uses": max_uses,
        "used_count": 0,
        "invite_type": invite_type,
        "is_active": True
    }

    await invitations_collection.insert_one(invitation_doc)

    return invitation_doc
