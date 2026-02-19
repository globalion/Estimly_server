from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from pymongo import ReturnDocument
from database.mongo import projects_collection, estimation_settings_collection
#from dependencies import get_current_user
from schemas.project import ProjectCreate, ProjectUpdate
from utils.normalize import normalize
from utils.serializers import serialize_ids_only
from services.resource_rates import get_resource_rate_map
from services.cost_timeline_engine import calculate_estimation
from utils.permissions import require_permission

router = APIRouter(prefix="/api/projects", tags=["Projects"])

# Create Project
@router.post("/")
async def create_project(
    payload: ProjectCreate,
    user=Depends(require_permission("projects.create"))
):
    name_norm = normalize(payload.name)
    client_norm = normalize(payload.client_name)

    existing = await projects_collection.find_one({
        "company_id": ObjectId(user["company_id"]),
        "name_normalized": name_norm,
        "client_name_normalized": client_norm
    })

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Project with same name already exists for this client"
        )

    now = datetime.utcnow()

    project_data = payload.model_dump(mode="json")

    rates = await get_resource_rate_map(user["company_id"])

    # Fetch company estimation settings
    settings = await estimation_settings_collection.find_one(
        {"company_id": ObjectId(user["company_id"])}
        )
    
    if not settings:
        raise HTTPException(
            status_code=500,
            detail="Estimation settings not configured for this company"
            )
    
    # calculate estimation while creating project
    estimation_result = calculate_estimation(project_data,rates,settings)

    project = {
        **project_data,

        "modules": [
            module.model_dump(mode="json") for module in payload.modules
        ],

        "estimation_snapshot": {
            **estimation_result,
            "calculated_at": now
        },

        "template_name": payload.template_name,
        "name_normalized": name_norm,
        "client_name_normalized": client_norm,
        "status": "draft",
        "company_id": ObjectId(user["company_id"]),
        "created_by": ObjectId(user["_id"]),
        "created_at": now,
        "updated_at": now
    }

    result = await projects_collection.insert_one(project)

    return {
        "message": "Project added successfully",
        "project_id": str(result.inserted_id)
    }


# Get All Projects
@router.get("/")
async def get_projects(
    page: int = 1,
    limit: int = 10,
    user=Depends(require_permission("projects.read"))
):

    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Invalid pagination params")

    skip = (page - 1) * limit

    cursor = (
        projects_collection
        .find({"company_id": ObjectId(user["company_id"])})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    projects = await cursor.to_list(length=limit)
    return [serialize_ids_only(p) for p in projects]


# Get Single Project
@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user=Depends(require_permission("projects.read"))
):

    project = await projects_collection.find_one({
        "_id": ObjectId(project_id),
        "company_id": ObjectId(user["company_id"])
    })

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return serialize_ids_only(project)


# Update Project
@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    user=Depends(require_permission("projects.update"))
):

    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    # Fetch existing project
    project = await projects_collection.find_one({
        "_id": ObjectId(project_id),
        "company_id": ObjectId(user["company_id"])
    })


    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    
    # Estimator cann not allowed to modify project if project status not under draft
    if user["role"] == "estimator" and project["status"] != "draft":
        raise HTTPException(
        status_code=403,
        detail="Estimator can only modify draft projects"
    )


    # Normalize basic fields
    if "name" in update_data:
        update_data["name_normalized"] = normalize(update_data["name"])

    if "client_name" in update_data:
        update_data["client_name_normalized"] = normalize(update_data["client_name"])

    if "status" in update_data:
        update_data["status"] = update_data["status"].strip().lower()


    # Detect estimation-impacting changes
    estimation_fields = {
        "modules",
        "target_margin",
        "risk_buffer",
        "negotiation_buffer",
        "estimated_team_size"
    }

    should_recalculate = any(
        field in update_data for field in estimation_fields
    )

    if should_recalculate:

        # Build clean calculation input
        calculation_input = {
            "modules": update_data.get("modules", project["modules"]),
            "target_margin": update_data.get("target_margin", project["target_margin"]),
            "risk_buffer": update_data.get("risk_buffer", project["risk_buffer"]),
            "negotiation_buffer": update_data.get("negotiation_buffer", project["negotiation_buffer"]),
            "estimated_team_size": update_data.get("estimated_team_size", project["estimated_team_size"]),
        }

        # Extract used roles
        used_roles = set()

        for module in calculation_input["modules"]:
            for feature in module["features"]:
                for task in feature["tasks"]:
                    used_roles.add(task["role"])


        # Preserve old snapshot rates
        old_snapshot = project.get("estimation_snapshot", {})
        old_rates = old_snapshot.get("rate_snapshot", {})
    
        # Fetch system rates
        system_rates = await get_resource_rate_map(user["company_id"])

        # Build new rate snapshot (only used roles)
        new_rate_snapshot = {}

        for role in used_roles:

            if role in old_rates:
                # Freeze old rate
                new_rate_snapshot[role] = old_rates[role]
            else:
                # Use system rate for new role
                if role not in system_rates:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No hourly rate found for role: {role}"
                    )
                new_rate_snapshot[role] = system_rates[role]


        # Fetch company estimation settings
        settings = await estimation_settings_collection.find_one(
            {"company_id": ObjectId(user["company_id"])}
            )
        
        if not settings:
            raise HTTPException(
                status_code=500,
                detail="Estimation settings not configured for this company"
                )

        # Recalculate estimation
        try:
            estimation = calculate_estimation(
                calculation_input,
                new_rate_snapshot,
                settings
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


        # Store new snapshot
        update_data["estimation_snapshot"] = {
            **estimation,
            "rate_snapshot": new_rate_snapshot,
            "calculated_at": datetime.utcnow()
        }

    update_data["updated_at"] = datetime.utcnow()

    # Update project in DB
    updated_project = await projects_collection.find_one_and_update(
        {
            "_id": ObjectId(project_id),
            "company_id": ObjectId(user["company_id"])
        },
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    return {
        "message": "Project updated successfully",
        "project": serialize_ids_only(updated_project)
    }



# Delete Project
@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user=Depends(require_permission("projects.delete"))
):

    result = await projects_collection.delete_one({
        "_id": ObjectId(project_id),
        "company_id": ObjectId(user["company_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted successfully"}
