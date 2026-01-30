from fastapi import APIRouter, Request, HTTPException
from utils.oauth import oauth
from database.mongo import users_collection
from utils.auth_jwt import create_access_token

router = APIRouter(prefix="/auth/social", tags=["Social Auth"])


@router.get("/{provider}")
async def social_login(provider: str, request: Request):
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(400, "Unsupported provider")

    redirect_uri = request.url_for("social_callback", provider=provider)
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback", name="social_callback")
async def social_callback(provider: str, request: Request):
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)

    # ---------- PROVIDER NORMALIZATION ----------
    if provider == "google":
        user = token["userinfo"]
        email = user["email"]
        name = user["name"]
        avatar = user.get("picture")
        provider_id = user["sub"]

    elif provider == "github":
        resp = await client.get("user", token=token)
        user = resp.json()
        email = user.get("email")
        name = user["login"]
        avatar = user.get("avatar_url")
        provider_id = str(user["id"])

    elif provider == "linkedin":
        user = token["userinfo"]
        email = user["email"]
        name = user["name"]
        avatar = None
        provider_id = user["sub"]

    else:
        raise HTTPException(400, "Invalid provider")

    # ---------- USER UPSERT ----------
    existing_user = users_collection.find_one({"email": email})

    if not existing_user:
        users_collection.insert_one({
            "email": email,
            "name": name,
            "avatar": avatar,
            "auth_type": "social",
            "social_accounts": {provider: provider_id},
            "is_active": True
        })
    else:
        users_collection.update_one(
            {"email": email},
            {"$set": {f"social_accounts.{provider}": provider_id}}
        )

    # ---------- JWT ----------
    access_token = create_access_token({"sub": email})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }