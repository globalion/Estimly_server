from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from bson import ObjectId

from database.mongo import users_collection
from utils.auth_jwt import SECRET_KEY, ALGORITHM

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await users_collection.find_one(
        {"_id": ObjectId(user_id)}
    )

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    user["id"] = str(user["_id"])
    user["_id"] = str(user["_id"])
    user["company_id"] = str(user["company_id"])

    return user
