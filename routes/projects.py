from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from pymongo import ReturnDocument

from database.mongo import projects_collection
from dependencies import get_current_user
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from utils.serializers import serialize_project

router = APIRouter(prefix="/projects", tags=["Projects"])

def normalize(text: str) -> str:
    return text.strip().lower()

# Create Project
@router.post("/", response_model=ProjectResponse)
async def create_project(
    payload: ProjectCreate,
    user=Depends(get_current_user)
):
    name_norm = normalize(payload.name)
    client_norm = normalize(payload.client_name)

    # Duplicate check (company scoped)
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

    project = {
        **payload.dict(),
        "name_normalized": name_norm,
        "client_name_normalized": client_norm,
        "status": "DRAFT",
        "company_id": ObjectId(user["company_id"]),
        "created_by": ObjectId(user["_id"]),
        "created_at": datetime.utcnow()
    }

    result = await projects_collection.insert_one(project)
    project["_id"] = result.inserted_id

    return serialize_project(project)


# Get All Projects
@router.get("/", response_model=list[ProjectResponse])
async def get_projects(
    page: int = 1,
    limit: int = 10,
    user=Depends(get_current_user)
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
    return [serialize_project(p) for p in projects]


# Get Single Project
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user=Depends(get_current_user)
):
    project = await projects_collection.find_one({
        "_id": ObjectId(project_id),
        "company_id": ObjectId(user["company_id"])
    })

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return serialize_project(project)


# Update Project
@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    user=Depends(get_current_user)
):
    update_data = payload.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    if "name" in update_data:
        update_data["name_normalized"] = normalize(update_data["name"])

    if "client_name" in update_data:
        update_data["client_name_normalized"] = normalize(update_data["client_name"])

    project = await projects_collection.find_one_and_update(
        {
            "_id": ObjectId(project_id),
            "company_id": ObjectId(user["company_id"])
        },
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return serialize_project(project)


# Delete Project
@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user=Depends(get_current_user)
):
    result = await projects_collection.delete_one({
        "_id": ObjectId(project_id),
        "company_id": ObjectId(user["company_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted successfully"}
