from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from database.mongo import estimation_techniques_collection
from utils.serializers import serialize_ids_only
from dependencies import get_current_user

router = APIRouter(
    prefix="/api/estimation-techniques",
    tags=["Estimation Techniques"]
)

# Get all ACTIVE estimation techniques
@router.get("/")
async def get_estimation_techniques(user=Depends(get_current_user)):
    cursor = estimation_techniques_collection.find(
        {"status": "active"},
        {
            "_id": 1,
            "name": 1,
            "standard": 1,
            "description": 1,
            "best_for": 1,
            "complexity": 1,
            "accuracy": 1
        }
    )

    techniques = await cursor.to_list(length=None)
    return [serialize_ids_only(t) for t in techniques]


# Get by ID
@router.get("/{technique_id}")
async def get_estimation_technique_by_id(
    technique_id: str,
    user=Depends(get_current_user)
):
    technique = await estimation_techniques_collection.find_one(
        {
            "_id": ObjectId(technique_id),
            "status": "active"
        }
    )

    if not technique:
        raise HTTPException(404, "Estimation technique not found")

    return serialize_ids_only(technique)
