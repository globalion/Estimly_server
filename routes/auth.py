from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from database.mongo import users_collection, companies_collection
from schemas.auth import SignupRequest, LoginRequest, UserResponse
from utils.security import hash_password, verify_password
from utils.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

def normalize(text: str) -> str:
    return text.strip().lower()

# Signup
@router.post("/signup", response_model=UserResponse)
async def signup(payload: SignupRequest):

    # 1. Email uniqueness
    existing_user = await users_collection.find_one(
        {"email": payload.email}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    company_name_norm = normalize(payload.company_name)

    # 2. Find company
    company = await companies_collection.find_one(
        {"name_normalized": company_name_norm}
    )

    # 3. Create company if not exists
    if not company:
        company_doc = {
            "name": payload.company_name,
            "name_normalized": company_name_norm,
            "created_at": datetime.utcnow()
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

# Login
@router.post("/login")
async def login(payload: LoginRequest):

    user = await users_collection.find_one(
        {"email": payload.email}
    )
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered. Please sign up first.")

    if not verify_password(payload.password, user["password_hash"]):
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
