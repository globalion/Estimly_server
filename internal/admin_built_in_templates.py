from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId

from database.mongo import built_in_templates_collection
from internal.admin_security import internal_admin_auth
from schemas.built_in_template import BuiltInTemplateCreate
from schemas.built_in_template import BuiltInTemplateUpdate
from utils.serializers import serialize_ids_only

admin_built_in_templates_router = APIRouter(
    prefix="/internal/admin/built-in-templates",
    tags=["Internal Admin • Built-in Templates"]
)

# Get
@admin_built_in_templates_router.get("")
async def get_all_built_in_templates(
    _=Depends(internal_admin_auth)
):
    templates = await built_in_templates_collection.find({}).to_list(length=None)
    return [serialize_ids_only(t) for t in templates]


@admin_built_in_templates_router.post("")
async def add_built_in_template(
    payload: BuiltInTemplateCreate,
    _=Depends(internal_admin_auth)
):
    exists = await built_in_templates_collection.find_one({
        "name": payload.name,
        "status": "active"
    })

    if exists:
        raise HTTPException(400, "Built-in template already exists")

    now = datetime.utcnow()

    doc = {
        "name": payload.name,
        "description": payload.description,
        "default_margin": payload.default_margin,
        "default_risk_buffer": payload.default_risk_buffer,
        "modules": [m.model_dump() for m in payload.modules],
        "add_ons": [a.model_dump() for a in payload.add_ons],
        "status": "active",
        "created_by": "system",
        "created_at": now,
        "updated_at": now
    }

    result = await built_in_templates_collection.insert_one(doc)

    return {
        "message": "Built-in template added successfully",
        "template_id": str(result.inserted_id)
    }



# # Post
# @admin_built_in_templates_router.post("")
# async def add_built_in_template(
#     payload: BuiltInTemplateCreate,
#     _=Depends(internal_admin_auth)
# ):
#     if not payload.name:
#         raise HTTPException(400, "Template name is required")

#     exists = await built_in_templates_collection.find_one({
#         "name": payload.name,
#         "status": "active"
#     })

#     if exists:
#         raise HTTPException(400, "Built-in template already exists")

#     doc = {
#         "_id": ObjectId(),
#         "name": payload.name,
#         "description": payload.description,
#         "modules": payload.modules,
#         "addons": [addon.dict() for addon in payload.addons], 
#         "default_margin": payload.default_margin,
#         "risk_buffer": payload.risk_buffer,
#         "status": "active",
#         "created_by": "estimly",
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }

#     await built_in_templates_collection.insert_one(doc)

#     return {
#         "message": "Built-in template added successfully",
#         "template_id": str(doc["_id"])
#     }


# Patch
@admin_built_in_templates_router.patch("/{template_id}")
async def patch_built_in_template(
    template_id: str,
    payload: BuiltInTemplateUpdate,
    _=Depends(internal_admin_auth)
):
    update_fields = payload.model_dump(exclude_unset=True)

    if not update_fields:
        raise HTTPException(400, "No valid fields provided for update")

    # addons are ALREADY dicts here → no conversion needed
    update_fields["updated_at"] = datetime.utcnow()

    result = await built_in_templates_collection.update_one(
        {"_id": ObjectId(template_id)},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Built-in template not found")

    return {"message": "Built-in template updated successfully"}




# Delete
@admin_built_in_templates_router.delete("/{template_id}")
async def delete_built_in_template(
    template_id: str,
    _=Depends(internal_admin_auth)
):
    result = await built_in_templates_collection.delete_one(
        {"_id": ObjectId(template_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(404, "Built-in template not found")

    return {"message": "Built-in template deleted successfully"}
