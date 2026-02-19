from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from pymongo import ReturnDocument
from utils.permissions import require_permission
from database.mongo import estimation_settings_collection
from utils.serializers import serialize_ids_only
from schemas.estimation_settings import EstimationSettingsUpdate


router = APIRouter(
    prefix="/api/settings/estimation",
    tags=["Estimation Settings"]
)

@router.get("/estimation")
async def get_estimation_settings(
    user=Depends(require_permission("estimation_settings.read"))
):

    settings = await estimation_settings_collection.find_one(
        {"company_id": ObjectId(user["company_id"])}
    )

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    return serialize_ids_only(settings)


@router.patch("/")
async def update_estimation_settings(
    payload: EstimationSettingsUpdate,
    user=Depends(require_permission("estimation_settings.update"))
):
    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    update_data["updated_at"] = datetime.utcnow()

    settings = await estimation_settings_collection.find_one_and_update(
        {"company_id": ObjectId(user["company_id"])},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    if not settings:
        raise HTTPException(status_code=404, detail="Estimation settings not found")

    return {
        "message": "Estimation settings updated successfully",
        "data": serialize_ids_only(settings)
    }
