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
from database.mongo import users_collection
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

 # ✅ HANDLE CANCEL / DENY FIRST
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error={provider}_cancelled"
        )
    
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)

    # --- Normalize provider data ---
    if provider == "google":
        userinfo = token["userinfo"]
        email = userinfo.get("email")
        name = userinfo.get("name")
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
            primary_email = next((e for e in emails if e.get("primary")), None)
            email = primary_email.get("email") if primary_email else None

        if not email:
            raise HTTPException(status_code=400, detail="Email not available from GitHub")

        name = userinfo.get("login")
        avatar = userinfo.get("avatar_url")
        provider_id = str(userinfo.get("id"))

    elif provider == "linkedin":
        userinfo = token["userinfo"]
        email = userinfo.get("email")
        name = userinfo.get("name")
        avatar = None
        provider_id = userinfo.get("sub")

    else:
        raise HTTPException(status_code=400, detail="Invalid provider")

  
    # --- UPSERT USER ---
    existing_user = await users_collection.find_one({"email": email})

    if not existing_user:
        await users_collection.insert_one({
            "email": email,
            "name": name,
            "avatar": avatar,
            "auth_type": "social",
            "social_accounts": {provider: provider_id},
            "is_active": True,
            "role": "USER"  # default role
        })
    else:
        await users_collection.update_one(
            {"email": email},
            {"$set": {f"social_accounts.{provider}": provider_id}}
        )
    # --- Fetch user from DB ---
    db_user = await users_collection.find_one({"email": email})

    # --- Create JWT token ---
    access_token = create_access_token({
        "user_id": str(db_user["_id"]),
        "company_id": str(db_user.get("company_id")) if db_user.get("company_id") else None,
        "role": db_user.get("role", "USER")
    })

    # --- Redirect to frontend with token ---
    return RedirectResponse(
   url=f"{FRONTEND_URL}/auth/social/callback"
    f"?token={access_token}"
    f"&user_id={db_user['_id']}"
    f"&email={email}"
    f"&role={db_user.get('role','USER')}"
    f"&message=Login successful"
)

