from fastapi import APIRouter, Depends
from bson import ObjectId
from dependencies import get_current_user
from database.mongo import projects_collection
from utils.serializers import serialize_ids_only

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
async def dashboard_summary(user=Depends(get_current_user)):
    company_id = ObjectId(user["company_id"])

    # Total projects of the company
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

    # Recent projects (last 5)
    recent_projects = await projects_collection.find(
        {"company_id": company_id},
        {
            "name": 1,
            "client_name": 1,
            "status": 1,
            "created_at": 1
        }
    ).sort("created_at", -1).limit(5).to_list(5)

    recent_projects = [serialize_ids_only(p) for p in recent_projects]

    return {
            "total_projects": total_projects,
            "status_distribution": status_distribution,
            "recent": recent_projects
    }
