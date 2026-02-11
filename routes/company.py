from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from database.mongo import companies_collection
from dependencies import get_current_user
from schemas.company import CompanyUpdate
from utils.normalize import normalize
from utils.serializers import serialize_ids_only

router = APIRouter(prefix="/api/company", tags=["Company"])

@router.get("/")
async def get_company(user=Depends(get_current_user)):
    company = await companies_collection.find_one(
        {"_id": ObjectId(user["company_id"])}
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return serialize_ids_only(company)


@router.patch("/")
async def update_company(
    payload: CompanyUpdate,
    user=Depends(get_current_user)
):
    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    if "name" in update_data:
        update_data["name_normalized"] = normalize(update_data["name"])

    update_data["updated_at"] = datetime.utcnow()

    company = await companies_collection.find_one_and_update(
        {"_id": ObjectId(user["company_id"])},
        {"$set": update_data},
        return_document=True
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return {
        "message": "Company data updated successfully",
        "data": serialize_ids_only(company)
    }
