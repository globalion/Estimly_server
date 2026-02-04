from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from dependencies import get_current_user
from database.mongo import projects_collection
from utils.serializers import serialize_ids_only

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
async def dashboard_summary(user=Depends(get_current_user)):

    # Guard for social-login users
    if not user.get("company_id"):
        raise HTTPException(
            status_code=400,
            detail="Company not assigned to user"
        )

    company_id = ObjectId(user["company_id"])

    # Total projects
    total_projects = await projects_collection.count_documents({
        "company_id": company_id
    })

    # Status distribution
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_data = await projects_collection.aggregate(pipeline).to_list(None)
    status_distribution = {item["_id"]: item["count"] for item in status_data}

    active_projects = (
    status_distribution.get("in_progress", 0) +
    status_distribution.get("approved", 0)
     )

    # Recent projects (NO recalculation)
    recent_projects = await projects_collection.find(
        {"company_id": company_id},
        {
            "name": 1,
            "client_name": 1,
            "status": 1,
            "updated_at": 1,
            "estimation_snapshot": 1
        }
    ).sort("updated_at", -1).limit(5).to_list(5)

    recent = []

    for project in recent_projects:
        project = serialize_ids_only(project)

        snapshot = project.get("estimation_snapshot")

        recent.append({
            "id": project["id"],
            "name": project["name"],
            "clientName": project.get("client_name"),
            "status": project.get("status"),
            "updated_at": project.get("updated_at"),
            "estimation_snapshot": snapshot
        })

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "status_distribution": status_distribution,
        "recent": recent
    }
