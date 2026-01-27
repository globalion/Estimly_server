from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from database.mongo import users_collection, companies_collection
from schemas.auth import SignupRequest, LoginRequest, UserResponse
from utils.security import hash_password, verify_password
from utils.auth_jwt import create_access_token
from utils.normalize import normalize
from utils.password_reset import create_reset_token, verify_reset_token
from utils.email import send_reset_email
from schemas.auth import ForgotPasswordRequest, ResetPasswordRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

# Signup Endpoint
@router.post("/signup", response_model=UserResponse)
async def signup(payload: SignupRequest):
    # 1. Check email uniqueness
    existing_user = await users_collection.find_one({"email": payload.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    company_name_norm = normalize(payload.company_name)

    # 2. Find company
    company = await companies_collection.find_one({"name_normalized": company_name_norm})

    now = datetime.utcnow()

    # 3. Create company if not exists
    if not company:
        company_doc = {
            "name": payload.company_name,
            "name_normalized": company_name_norm,
            "industry": None,
            "company_size": None,
            "currency": "USD",
            "date_format": "MM/DD/YYYY",
            "timezone": "UTC",
            "created_at": now,
            "updated_at": now
        }
        company_result = await companies_collection.insert_one(company_doc)
        company_id = company_result.inserted_id
        role = "ADMIN"
    else:
        company_id = company["_id"]
        role = "USER"

    # 4. Create user
    user_doc = {
        "full_name": payload.full_name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": role,
        "company_id": company_id,
        "created_at": datetime.utcnow()
    }
    user_result = await users_collection.insert_one(user_doc)

    return UserResponse(
        id=str(user_result.inserted_id),
        full_name=user_doc["full_name"],
        email=user_doc["email"],
        role=user_doc["role"],
        company_id=str(company_id)
    )


# Login Endpoint
@router.post("/login")
async def login(payload: LoginRequest):
    user = await users_collection.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": str(user["_id"]),
        "company_id": str(user["company_id"]),
        "role": user["role"]
    })

    return {
        "access_token": token,
        "user": {
            "id": str(user["_id"]),
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "company_id": str(user["company_id"])
        }
    }


# Forgot Password
@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    user = await users_collection.find_one({"email": payload.email})
    
    # Security: always respond the same
    if not user:
        return {"success": False, "message": "Email is not registered"}

    # Generate JWT reset token
    token = create_reset_token(payload.email)

    reset_link = f"http://localhost:3000/reset-password?token={token}"

    # Send reset email
    await send_reset_email(payload.email, reset_link)

    return {"success": True, "message": "Reset link sent to your email"}


# Reset Password
@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    email = verify_reset_token(payload.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": hash_password(payload.new_password)}}
    )

    return {"success": True, "message": "Password reset successfully"}  
