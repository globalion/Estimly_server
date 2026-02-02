from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database.mongo import users_collection
from dependencies import get_current_user

router = APIRouter(
    prefix="/api/user",
    tags=["User"]
)

@router.get("/")
async def get_user_info(
    user=Depends(get_current_user)
):
    db_user = await users_collection.find_one(
        {"_id": ObjectId(user["user_id"])},   
        {"full_name": 1, "role": 1}
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": db_user["full_name"],
        "role": db_user["role"]
    }
