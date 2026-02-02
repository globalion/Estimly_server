# from fastapi import APIRouter, Request, HTTPException
# from utils.oauth import oauth
# from database.mongo import users_collection
# from utils.auth_jwt import create_access_token

# router = APIRouter(prefix="/auth/social", tags=["Social Auth"])


# @router.get("/{provider}")
# async def social_login(provider: str, request: Request):
#     client = oauth.create_client(provider)
#     if not client:
#         raise HTTPException(400, "Unsupported provider")

#     redirect_uri = request.url_for("social_callback", provider=provider)
#     return await client.authorize_redirect(request, redirect_uri)


# @router.get("/{provider}/callback", name="social_callback")
# async def social_callback(provider: str, request: Request):
#     client = oauth.create_client(provider)
#     token = await client.authorize_access_token(request)

#     # ---------- PROVIDER NORMALIZATION ----------
#     if provider == "google":
#         user = token["userinfo"]
#         email = user["email"]
#         name = user["name"]
#         avatar = user.get("picture")
#         provider_id = user["sub"]

#     elif provider == "github":
#         resp = await client.get("user", token=token)
#         user = resp.json()
#         email = user.get("email")
#         name = user["login"]
#         avatar = user.get("avatar_url")
#         provider_id = str(user["id"])

#     elif provider == "linkedin":
#         user = token["userinfo"]
#         email = user["email"]
#         name = user["name"]
#         avatar = None
#         provider_id = user["sub"]

#     else:
#         raise HTTPException(400, "Invalid provider")

#     # ---------- USER UPSERT ----------
#     existing_user = users_collection.find_one({"email": email})

#     if not existing_user:
#         users_collection.insert_one({
#             "email": email,
#             "name": name,
#             "avatar": avatar,
#             "auth_type": "social",
#             "social_accounts": {provider: provider_id},
#             "is_active": True
#         })
#     else:
#         users_collection.update_one(
#             {"email": email},
#             {"$set": {f"social_accounts.{provider}": provider_id}}
#         )

#     # ---------- JWT ----------
#     access_token = create_access_token({"sub": email})

#     return {
#         "access_token": access_token,
#         "token_type": "bearer"
#     }

# backend/routes/social_auth.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from bson import ObjectId
from database.mongo import users_collection, companies_collection
from datetime import datetime
from utils.oauth import oauth
from utils.auth_jwt import create_access_token
import os

router = APIRouter(prefix="/auth/social", tags=["Social Auth"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/{provider}")
async def social_login(provider: str, request: Request):
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    redirect_uri = request.url_for("social_callback", provider=provider)

    if provider == "google":
        return await client.authorize_redirect(
            request,
            redirect_uri,
            prompt="consent",
            access_type="offline",
            include_granted_scopes="true"
        )

    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback", name="social_callback")
async def social_callback(provider: str, request: Request):
    # --- HANDLE CANCEL / DENY ---
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error={provider}_cancelled"
        )

    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)

    # --- NORMALIZE PROVIDER DATA ---
    email = full_name = avatar = provider_id = None

    if provider == "google":
        userinfo = token.get("userinfo", {})
        email = userinfo.get("email")
        full_name = userinfo.get("name")
        avatar = userinfo.get("picture")
        provider_id = userinfo.get("sub")

    elif provider == "github":
        resp = await client.get("user", token=token)
        userinfo = resp.json()
        email = userinfo.get("email")

        # GitHub sometimes hides email
        if not email:
            emails_resp = await client.get("user/emails", token=token)
            emails = emails_resp.json()
            primary_email = next((e for e in emails if e.get("primary") and e.get("verified")), None)
            email = primary_email.get("email") if primary_email else None

        if not email:
            raise HTTPException(status_code=400, detail="Email not available from GitHub")

        full_name = userinfo.get("name") or userinfo.get("login")  # fallback to login
        avatar = userinfo.get("avatar_url")
        provider_id = str(userinfo.get("id"))

    elif provider == "linkedin":
        userinfo = token.get("userinfo", {})
        email = userinfo.get("email")
        full_name = userinfo.get("name")
        avatar = None
        provider_id = userinfo.get("sub")

    else:
        raise HTTPException(status_code=400, detail="Invalid provider")

    if not email or not full_name or not provider_id:
        raise HTTPException(status_code=400, detail="Failed to fetch user info from provider")

    # --- UPSERT USER ---
    existing_user = await users_collection.find_one({"email": email})

    if not existing_user:
        result = await users_collection.insert_one({
            "email": email,
            "full_name": full_name,
            "avatar": avatar,
            "auth_type": "social",
            "social_accounts": {provider: provider_id},
            "is_active": True,
            "role": "USER"
        })
        user_id = result.inserted_id
    else:
        await users_collection.update_one(
            {"email": email},
            {"$set": {f"social_accounts.{provider}": provider_id}}
        )
        user_id = existing_user["_id"]

    db_user = await users_collection.find_one({"_id": user_id})

    # --- ENSURE COMPANY EXISTS ---
    if not db_user.get("company_id"):
        company_doc = {
            "name": f"{db_user.get('full_name', 'User')}'s Company",
            "owner_id": db_user["_id"],
            "created_at": datetime.utcnow()
        }
        company_result = await companies_collection.insert_one(company_doc)
        company_id = company_result.inserted_id
        await users_collection.update_one(
            {"_id": db_user["_id"]},
            {"$set": {"company_id": company_id}}
        )
        db_user = await users_collection.find_one({"_id": db_user["_id"]})

    # --- CREATE JWT TOKEN ---
    access_token = create_access_token({
        "user_id": str(db_user["_id"]),
        "company_id": str(db_user["company_id"]),
        "role": db_user.get("role", "USER")
    })

    return RedirectResponse(
        url=f"{FRONTEND_URL}/auth/social/callback"
            f"?token={access_token}"
            f"&user_id={db_user['_id']}"
            f"&email={email}"
            f"&role={db_user.get('role','USER')}"
            f"&message=Login successful"
    )

