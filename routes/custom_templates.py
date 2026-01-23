from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from pymongo import ReturnDocument
from schemas.custom_template import CustomTemplateCreate
from schemas.custom_template import CustomTemplateUpdate
from database.mongo import custom_templates_collection
from utils.serializers import serialize_ids_only
from dependencies import get_current_user

router = APIRouter(prefix="/api/custom-templates", tags=["Templates"])

# Create Template
@router.post("/")
async def create_custom_template(
    payload: CustomTemplateCreate,
    user=Depends(get_current_user)
):
    # if user["role"] not in ["manager", "company_admin"]:
    #     raise HTTPException(403, "Permission denied")

    template_doc = {
        "name": payload.name,
        "description": payload.description,
        "default_margin": payload.default_margin,
        "default_risk_buffer": payload.default_risk_buffer,
        "modules": [module.dict() for module in payload.modules],
        "status": "active",
        "company_id": ObjectId(user["company_id"]),
        "created_by": ObjectId(user["id"]),
        "created_at": datetime.utcnow()
    }

    result = await custom_templates_collection.insert_one(template_doc)

    return {
        "message": "Custom template created",
        "template_id": str(result.inserted_id)
    }


# Get All Templates
@router.get("/")
async def get_custom_templates(
    page: int = 1,
    limit: int = 10,
    user=Depends(get_current_user)
):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination params")

    skip = (page - 1) * limit

    cursor = (
        custom_templates_collection
        .find({"company_id": ObjectId(user["company_id"])})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    templates = await cursor.to_list(length=limit)
    return [serialize_ids_only(t) for t in templates]


# Get Single Template
@router.get("/{template_id}")
async def get_custom_template_by_id(
    template_id: str,
    user=Depends(get_current_user)
):
    try:
        template = await custom_templates_collection.find_one({
            "_id": ObjectId(template_id),
            "company_id": ObjectId(user["company_id"])
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return serialize_ids_only(template)


# Update Template
@router.patch("/{template_id}")
async def update_custom_template(
    template_id: str,
    payload: CustomTemplateUpdate,
    user=Depends(get_current_user)
):
   # Extract only fields sent by frontend
    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")

    update_data["updated_at"] = datetime.utcnow()

    # Update and return updated document in ONE db call
    template = await custom_templates_collection.find_one_and_update(
        {
            "_id": ObjectId(template_id),
            "company_id": ObjectId(user["company_id"])
        },
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "message": "Template updated successfully",
        "data": serialize_ids_only(template)
    }


# Delete Template
@router.delete("/{template_id}")
async def delete_custom_template(
    template_id: str,
    user=Depends(get_current_user)
):
    try:
        result = await custom_templates_collection.delete_one({
            "_id": ObjectId(template_id),
            "company_id": ObjectId(user["company_id"])
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid template ID")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")

    return {"message": "Custom template deleted successfully"}
