from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from database.mongo import users_collection, companies_collection, estimation_settings_collection, client
from schemas.auth import SignupRequest, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from utils.security import hash_password, verify_password, validate_strong_password
from utils.auth_jwt import create_access_token
from utils.normalize import normalize
from utils.password_reset import create_reset_token, verify_reset_token
from utils.email import send_reset_email

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/pre-signup/send-otp")
async def pre_signup_send_otp(email: str):
    email_norm = email.strip().lower()
    
    # Check if email is already registered
    existing_user = await users_collection.find_one({"email": email_norm})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    otp = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)

    # Upsert OTP in pending_verifications
    await pending_verifications_collection.update_one(
        {"email": email_norm},
        {"$set": {"otp": otp, "expiry": expiry, "created_at": datetime.utcnow()}},
        upsert=True
    )

    await send_verification_otp(email_norm, otp)

    return {"message": "OTP sent successfully"}

@router.post("/pre-signup/verify-otp")
async def pre_signup_verify_otp(email: str, otp: str):
    email_norm = email.strip().lower()

    record = await pending_verifications_collection.find_one({"email": email_norm})

    if not record:
        raise HTTPException(status_code=404, detail="No OTP found for this email")

    if record["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if datetime.utcnow() > record["expiry"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    # ✅ Mark as verified instead of deleting
    await pending_verifications_collection.update_one(
        {"email": email_norm},
        {"$set": {"is_verified": True}, "$unset": {"otp": "", "expiry": ""}}
    )

    return {"message": "Email verified successfully"}

# Signup Endpoint
@router.post("/signup")
async def signup(payload: SignupRequest):

     #  Check if email was verified via pre-signup OTP
    verified = await pending_verifications_collection.find_one({
        "email": payload.email,
        "is_verified": True
    })
    if not verified:
        raise HTTPException(
            status_code=400,
            detail="Email not verified. Please verify before signing up."
        )
    
    validate_strong_password(payload.password)

    # Check if email already exists
    existing_user = await users_collection.find_one({"email": payload.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Normalize company name for consistent comparison
    company_name_norm = normalize(payload.company_name)

    # Check if company already exists
    existing_company = await companies_collection.find_one(
        {"name_normalized": company_name_norm}
    )

    # Prevent auto-joining existing company
    if existing_company:
        raise HTTPException(
            status_code=400,
            detail="Company already registered. Please contact your administrator."
        )

    now = datetime.utcnow()

    # Apply MongoDB transaction
    async with await client.start_session() as session:
        async with session.start_transaction():

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

            company_result = await companies_collection.insert_one(
                company_doc,
                session=session
            )
            company_id = company_result.inserted_id

            estimation_settings_doc = {
                "company_id": company_id,
                "complexity_multipliers": {
                    "low": 1.0,
                    "medium": 1.3,
                    "high": 1.6,
                    "extreme": 2.0
                },
                "productivity_factor": 0.85,
                "sprint_duration_weeks": 2,
                "working_hours_per_day": 8,
                "working_days_per_week": 5,
                "created_at": now,
                "updated_at": now
            }

            await estimation_settings_collection.insert_one(
                estimation_settings_doc,
                session=session
            )

            user_doc = {
                "full_name": payload.full_name,
                "email": payload.email,
                "password_hash": hash_password(payload.password),
                "role": "owner",
                "company_id": company_id,
                "failed_attempts": 0,
                "lock_until": None,
                "is_deleted": False,
                "deleted_at": None,
                "deleted_by": None,
                "created_at": now
            }

            await users_collection.insert_one(
                user_doc,
                session=session
            )

    return {
        "message": "Company and Owner account created successfully"
    }


# Login Endpoint
@router.post("/login")
async def login(payload: LoginRequest):
    user = await users_collection.find_one({
        "email": payload.email,
        "is_deleted": {"$ne": True}
        })

    if not user:
        raise HTTPException(status_code=400, detail="Email is not Registered")

    now = datetime.now(timezone.utc)

    # Check if locked
    lock_until = user.get("lock_until")
    
    if lock_until and now < lock_until:
        remaining_seconds = int((lock_until - now).total_seconds())
        remaining_minutes = max(1, remaining_seconds // 60)
        raise HTTPException(
            status_code=403,
            detail=f"Account temporarily locked due to multiple failed attempts. Try again in {remaining_minutes} minutes."
            )

    # Incorrect password
    if not verify_password(payload.password, user["password_hash"]):

        failed_attempts = user.get("failed_attempts", 0) + 1
        update_data = {"failed_attempts": failed_attempts}

        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            update_data["lock_until"] = now + timedelta(minutes=LOCK_DURATION_MINUTES)
            update_data["failed_attempts"] = 0

        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )

        raise HTTPException(status_code=401, detail="Inpassword")

    # Success
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"failed_attempts": 0, "lock_until": None}}
    )

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
    user = await users_collection.find_one({"email": payload.email, "is_deleted": {"$ne": True}})
    
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

    user = await users_collection.find_one({"email": email, "is_deleted": {"$ne": True}})
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    
    validate_strong_password(payload.new_password)

    # new password should not be same as old password
    if verify_password(payload.new_password, user["password_hash"]):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as your old password"
        )

    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
            "password_hash": hash_password(payload.new_password),
            "updated_at": datetime.utcnow()
        } })

    return {"success": True, "message": "Password reset successfully"}  
