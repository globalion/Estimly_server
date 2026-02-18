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

from schemas.user import UpdateUserRequest
from utils.permissions import require_permission, USER_ROLES

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

# company users
@router.get("/list")
async def get_company_users(
    current_user=Depends(require_permission("users.read"))
):

    company_id = ObjectId(current_user["company_id"])

    cursor = users_collection.find(
        {"company_id": company_id},
        {
            "full_name": 1,
            "email": 1,
            "role": 1
        }
    )

    users = await cursor.to_list(length=200)

    return {
        "users": [
            {
                "id": str(user["_id"]),
                "full_name": user.get("full_name"),
                "email": user.get("email"),
                "role": user.get("role")
            }
            for user in users
        ]
    }


# get single user
@router.get("/{user_id}")
async def get_single_user(
    user_id: str,
    current_user=Depends(require_permission("users.read"))
):
    # Validate user_id format
    try:
        target_user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    company_id = ObjectId(current_user["company_id"])

    # Fetch user from same company
    user = await users_collection.find_one(
        {
            "_id": target_user_id,
            "company_id": company_id
        },
        {
            "full_name": 1,
            "email": 1,
            "role": 1
        }
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user["_id"]),
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "role": user.get("role")
    }


# update company user
@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    current_user=Depends(require_permission("users.manage"))
):
    company_id = ObjectId(current_user["company_id"])

    # Validate user_id
    try:
        target_user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Fetch target user
    target_user = await users_collection.find_one({
        "_id": target_user_id,
        "company_id": company_id
    })

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Extract only provided fields
    update_fields = payload.dict(exclude_unset=True)

    # Handle full_name update
    if "full_name" in update_fields:
        name = update_fields["full_name"].strip()

        if len(name) < 2:
            raise HTTPException(
            status_code=400,
            detail="Full name must be at least 2 characters")
        
        if len(name) > 100:
            raise HTTPException(
            status_code=400,
            detail="Full name cannot exceed 100 characters")
        
        
        update_fields["full_name"] = name


    # Handle role update
    if "role" in update_fields:

        new_role = update_fields["role"]

        if new_role not in USER_ROLES.values():
            raise HTTPException(status_code=400, detail="Invalid role")

        current_role = current_user["role"]
        target_role = target_user["role"]

        # Admin restrictions
        if current_role == "admin":

            if target_role == "owner":
                raise HTTPException(
                    status_code=403,
                    detail="Admin cannot modify Owner"
                )

            if new_role == "owner":
                raise HTTPException(
                    status_code=403,
                    detail="Admin cannot assign Owner role"
                )

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="No valid fields provided for update"
        )

    await users_collection.update_one(
        {"_id": target_user_id},
        {"$set": update_fields}
    )

    return {"message": "User updated successfully"}



# delete user
@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user=Depends(require_permission("users.delete"))
):

    company_id = ObjectId(current_user["company_id"])

    # Validate ObjectId
    try:
        target_user_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Fetch target user
    target_user = await users_collection.find_one({
        "_id": target_user_id,
        "company_id": company_id
    })

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self delete
    if str(target_user["_id"]) == current_user["_id"]:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete yourself"
        )

    current_role = current_user["role"]
    target_role = target_user["role"]

    # Admin restrictions
    if current_role == "admin" and target_role == "owner":
        raise HTTPException(
            status_code=403,
            detail="Admin cannot delete Owner"
        )

    # Prevent deleting last owner
    if target_role == "owner":

        owner_count = await users_collection.count_documents({
            "company_id": company_id,
            "role": "owner"
        })

        if owner_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last owner of the company"
            )

    await users_collection.delete_one({
        "_id": target_user_id
    })

    return {"message": "User permanently deleted successfully"}


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
