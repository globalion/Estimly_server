from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database.mongo import projects_collection
from dependencies import get_current_user

router = APIRouter(prefix="/api/analytics",tags=["Advanced Analytics"])

@router.get("/summary")
async def get_analytics_summary(user=Depends(get_current_user)):

    try:
        company_object_id = ObjectId(user["company_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    pipeline = [
        {
            "$match": {
                "company_id": company_object_id
            }
        },
        {
            "$group": {
                "_id": None,
                "total_revenue": {
                    "$sum": {"$ifNull": ["$estimation_snapshot.total_revenue", 0]}
                },
                "total_cost": {
                    "$sum": {"$ifNull": ["$estimation_snapshot.total_cost", 0]}
                },
                "total_hours": {
                    "$sum": {"$ifNull": ["$estimation_snapshot.total_hours", 0]}
                },
                "total_projects": {"$sum": 1}
            }
        }
    ]

    cursor = projects_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        return {
            "total_projects": 0,
            "total_revenue": 0,
            "total_cost": 0,
            "total_profit": 0,
            "avg_margin_percent": 0,
            "total_hours": 0,
            "person_months": 0
        }

    data = result[0]

    total_revenue = data.get("total_revenue", 0)
    total_cost = data.get("total_cost", 0)
    total_hours = data.get("total_hours", 0)
    total_projects = data.get("total_projects", 0)

    total_profit = total_revenue - total_cost
    avg_margin = (total_profit / total_cost * 100) if total_cost else 0   #Margin % = (Profit / cost) × 100
    person_months = round(total_hours / 160, 2) if total_hours else 0  #Assume 1 person month = 160 hours

    return {
        "total_projects": total_projects,
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "total_profit": round(total_profit, 2),
        "avg_margin_percent": round(avg_margin, 2),
        "total_hours": round(total_hours, 2),
        "person_months": person_months
    }

