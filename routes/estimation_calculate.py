from fastapi import APIRouter, Depends
from services.cost_timeline_engine import calculate_estimation
from schemas.project import EstimationProjectRequest
from dependencies import get_current_user

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
    result = calculate_estimation(project)

    return result
