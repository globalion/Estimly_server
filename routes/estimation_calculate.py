from fastapi import APIRouter, Depends
from services.cost_timeline_engine import calculate_estimation
from schemas.project import EstimationProjectRequest
from dependencies import get_current_user
from services.resource_rates import get_resource_rate_map
from services.cost_timeline_engine import calculate_estimation

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
    rates = await get_resource_rate_map(user["company_id"])
    result = calculate_estimation(project, rates)

    return result
