from fastapi import APIRouter, HTTPException
from database.mongo import (
    estimation_techniques_collection,
    estimation_technique_info_collection,
    estimation_settings_collection
)

router = APIRouter(
    prefix="/estimation",
    tags=["Estimation"]
)

@router.get("/techniques")
async def get_estimation_techniques():
    techniques = []
    async for doc in estimation_techniques_collection.find({}, {"_id": 0}):
        techniques.append(doc)
    return techniques

@router.get("/techniques/{technique_key}")
async def get_technique_info(technique_key: str):
    doc = await estimation_technique_info_collection.find_one(
        {"technique_key": technique_key},
        {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Estimation technique not found")
    return doc

@router.get("/settings")
async def get_estimation_settings():
    settings = await estimation_settings_collection.find_one({}, {"_id": 0})
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not configured")
    return settings

@router.put("/settings")
async def update_estimation_settings(payload: dict):
    await estimation_settings_collection.update_one(
        {},
        {"$set": payload},
        upsert=True
    )
    return {"message": "Estimation settings updated successfully"}

