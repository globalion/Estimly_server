""" This is for checking calculation engine"""

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from services.cost_timeline_engine import calculate_estimation
from schemas.project import EstimationProjectRequest
from dependencies import get_current_user
from services.resource_rates import get_resource_rate_map
from database.mongo import estimation_settings_collection


router = APIRouter(
    prefix="/api/estimation",
    tags=["Estimation"]
)


@router.post("/calculate")
async def calculate_project_estimation(
    payload: EstimationProjectRequest,
    user=Depends(get_current_user)
):
    project = payload.model_dump()

    # Fetch resource rates
    rates = await get_resource_rate_map(user["company_id"])

    # Fetch estimation settings 
    settings = await estimation_settings_collection.find_one(
        {"company_id": ObjectId(user["company_id"])}
    )

    if not settings:
        raise HTTPException(
            status_code=500,
            detail="Estimation settings not configured for this company"
        )

    result = calculate_estimation(project, rates, settings)

    return result
