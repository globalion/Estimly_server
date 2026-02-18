from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId
import secrets

from database.mongo import users_collection, invites_collection
from dependencies import get_current_user
from schemas.invite import InviteRequest, AcceptInviteRequest
from utils.email import send_invite_email

from pymongo import ReturnDocument
from utils.security import hash_password
from utils.auth_jwt import create_access_token
from utils.permissions import require_permission

router = APIRouter(
    prefix="/api/user",
    tags=["User"]
)


@router.get("/")
async def get_user_info(
    user=Depends(get_current_user)
):
    db_user = await users_collection.find_one(
        {"_id": ObjectId(user["_id"])},   
        {"full_name": 1, "role": 1}
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": db_user["full_name"],
        "role": db_user["role"]
    }



@router.post("/invite")
async def invite_user(
    payload: InviteRequest,
    current_user=Depends(require_permission("users.invite"))
):

    role = current_user["role"]

    # Prevent admin from inviting Owner
    if role == "admin" and payload.role == "owner":
        raise HTTPException(
            status_code=403,
            detail="Admin cannot invite Owner"
        )

    # Check if user already exists
    existing_user = await users_collection.find_one({"email": payload.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")

    now = datetime.utcnow()

    # Check for existing active invite
    existing_invite = await invites_collection.find_one({
        "email": payload.email,
        "company_id": ObjectId(current_user["company_id"]),
        "is_used": False,
        "expires_at": {"$gt": now}
    })

    if existing_invite:
        token = existing_invite["token"]
    else:
        token = secrets.token_urlsafe(32)

        invite_doc = {
            "token": token,
            "company_id": ObjectId(current_user["company_id"]),
            "email": payload.email,
            "role": payload.role,
            "expires_at": now + timedelta(hours=48),
            "is_used": False,
            "created_at": now
        }

        await invites_collection.insert_one(invite_doc)

    invite_link = f"http://localhost:3000/accept-invite?token={token}"


    try:
        await send_invite_email(
            email=payload.email,
            invite_link=invite_link,
            role=payload.role
        )
    except Exception as e:
        print("Invite email failed:", str(e))

    return {"message": "Invite sent successfully"}



@router.post("/accept-invite")
async def accept_invite(payload: AcceptInviteRequest):

    now = datetime.utcnow()

    invite = await invites_collection.find_one_and_update(
        {
            "token": payload.token,
            "is_used": False,
            "expires_at": {"$gt": now}
        },
        {"$set": {"is_used": True}},
        return_document=ReturnDocument.AFTER
    )

    if not invite:
        raise HTTPException(
            status_code=400,
            detail="Invalid, expired, or already used invite token"
        )

    # Ensure email not registered
    existing_user = await users_collection.find_one({"email": invite["email"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create user
    user_doc = {
        "full_name": payload.full_name,
        "email": invite["email"],
        "password_hash": hash_password(payload.password),
        "role": invite["role"],
        "company_id": invite["company_id"],
        "created_at": now
    }

    result = await users_collection.insert_one(user_doc)

    # Generate JWT
    access_token = create_access_token({
        "user_id": str(result.inserted_id),
        "company_id": str(invite["company_id"]),
        "role": invite["role"]
    })

    return {
        "message": "Account created successfully",
        "access_token": access_token
    }
