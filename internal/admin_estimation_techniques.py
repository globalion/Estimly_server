from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId

from database.mongo import estimation_techniques_collection
from internal.admin_security import internal_admin_auth
from schemas.estimation_technique import (
    EstimationTechniqueCreate,
    EstimationTechniqueUpdate
)
from utils.serializers import serialize_ids_only


admin_estimation_techniques_router = APIRouter(
    prefix="/internal/admin/estimation-techniques",
    tags=["Internal Admin • Estimation Techniques"]
)


@admin_estimation_techniques_router.get("")
async def get_all_estimation_techniques(
    _=Depends(internal_admin_auth)
):
    techniques = await estimation_techniques_collection.find({}).to_list(length=None)
    return [serialize_ids_only(t) for t in techniques]


@admin_estimation_techniques_router.post("")
async def add_estimation_technique(
    payload: EstimationTechniqueCreate,
    _=Depends(internal_admin_auth)
):
    exists = await estimation_techniques_collection.find_one({
        "name": payload.name,
        "status": "active"
    })

    if exists:
        raise HTTPException(400, "Estimation technique already exists")

    now = datetime.utcnow()

    doc = {
        "name": payload.name,
        "standard": payload.standard,
        "description": payload.description,
        "use_cases": payload.use_cases,
        "complexity": payload.complexity,
        "time_required": payload.time_required,
        "accuracy": payload.accuracy,
        "status": "active",
        "created_by": "system",
        "created_at": now,
        "updated_at": now
    }

    result = await estimation_techniques_collection.insert_one(doc)

    return {
        "message": "Estimation technique added successfully",
        "technique_id": str(result.inserted_id)
    }


@admin_estimation_techniques_router.patch("/{technique_id}")
async def patch_estimation_technique(
    technique_id: str,
    payload: EstimationTechniqueUpdate,
    _=Depends(internal_admin_auth)
):
    update_fields = payload.model_dump(exclude_unset=True)

    if not update_fields:
        raise HTTPException(400, "No valid fields provided for update")

    update_fields["updated_at"] = datetime.utcnow()

    result = await estimation_techniques_collection.update_one(
        {"_id": ObjectId(technique_id)},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Estimation technique not found")

    return {"message": "Estimation technique updated successfully"}


@admin_estimation_techniques_router.delete("/{technique_id}")
async def delete_estimation_technique(
    technique_id: str,
    _=Depends(internal_admin_auth)
):
    result = await estimation_techniques_collection.delete_one(
        {"_id": ObjectId(technique_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(404, "Estimation technique not found")

    return {"message": "Estimation technique deleted successfully"}
