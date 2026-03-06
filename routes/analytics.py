from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database.mongo import projects_collection
from datetime import datetime, timedelta
from dependencies import get_current_user
import math


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
                "$sum": {"$ifNull": ["$estimation_snapshot.pricing.final_price", 0]}
            },
            "total_cost": {
                "$sum": {"$ifNull": ["$estimation_snapshot.totals.base_cost", 0]}
            },
            "total_hours": {
                "$sum": {"$ifNull": ["$estimation_snapshot.totals.hours", 0]}
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

    # ROUND FIRST
    total_revenue = round(total_revenue)
    total_cost = round(total_cost)
    total_hours = float(total_hours)
    
    
    total_profit = total_revenue - total_cost
    avg_margin = (total_profit / total_cost * 100) if total_cost else 0   #Margin % = (Profit / cost) × 100
    person_months = math.ceil(total_hours / 160) if total_hours else 0  #Assume 1 person month = 160 hours
    
    return {
    "total_projects": total_projects,
    "total_revenue": f"${total_revenue:,}",
    "total_cost": f"${total_cost:,}",
    "total_profit": f"${total_profit:,}",
    "avg_margin_percent": f"{round(avg_margin,1)}%",
    "total_hours": round(total_hours,2),
    "person_months": person_months
}

@router.get("/revenue-trend")
async def revenue_trend(user=Depends(get_current_user)):

    try:
        company_object_id = ObjectId(user["company_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid company id")

    six_months_ago = datetime.utcnow() - timedelta(days=180)

    pipeline = [

        {
            "$match": {
                "company_id": company_object_id,
                "created_at": {"$gte": six_months_ago}
            }
        },

        {
            "$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"}
                },

                "revenue": {
                    "$sum": {
                        "$ifNull": ["$estimation_snapshot.pricing.final_price", 0]
                    }
                },

                "cost": {
                    "$sum": {
                        "$ifNull": ["$estimation_snapshot.totals.base_cost", 0]
                    }
                },

                "projects": {"$sum": 1}
            }
        },

        {"$sort": {"_id.year": 1, "_id.month": 1}}

    ]

    result = await projects_collection.aggregate(pipeline).to_list(None)

    data = []

    for r in result:

        revenue = round(r.get("revenue", 0))
        cost = round(r.get("cost", 0))
        projects = r.get("projects", 0)

        data.append({
            "month": f"{r['_id']['year']}-{str(r['_id']['month']).zfill(2)}-01",
            "revenue": revenue,
            "cost": cost,
            "profit": revenue - cost,
            "projects": projects
        })

    return data

@router.get("/margin-analysis")
async def margin_analysis(user=Depends(get_current_user)):

    company_id = ObjectId(user["company_id"])

    pipeline = [

        {
            "$match": {
                "company_id": company_id
            }
        },

        {
            "$addFields": {
                "revenue": {"$ifNull": ["$estimation_snapshot.pricing.final_price", 0]},
                "cost": {"$ifNull": ["$estimation_snapshot.totals.base_cost", 0]},
                "hours": {"$ifNull": ["$estimation_snapshot.totals.hours", 0]},
                "status": {"$ifNull": ["$status", "draft"]},
                "target_margin": {"$ifNull": ["$target_margin",0]},
            }
        },

        {
            "$addFields": {
                "profit": {"$subtract": ["$revenue", "$cost"]},
                "marginPercent": {
                    "$cond": [
                        {"$gt": ["$cost", 0]},   # divide by cost
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        {"$subtract": ["$revenue", "$cost"]},
                                        "$cost"
                                    ]
                                },
                                100
                            ]
                        },
                        0
                    ]
                }
            }
        },

        {
            "$project": {
                "_id": 0,
                "project": "$name",
                "revenue": {"$round": ["$revenue", 2]},
                "cost": {"$round": ["$cost", 2]},
                "profit": {"$round": ["$profit", 2]},
                "marginPercent": {"$round": ["$marginPercent", 2]},
                "hours": {"$round": ["$hours", 2]},
                "status": 1,
                "target_margin": {"$round": ["$target_margin", 2]}
            }
        }

    ]

    projects = await projects_collection.aggregate(pipeline).to_list(length=None)

    return {
        "projects": projects
    }

@router.get("/project-timeline")
async def project_timeline(status: str = None):

    pipeline = []

    # Filter by status if provided
    if status:
        pipeline.append({
            "$match": {"status": status}
        })

    pipeline.extend([
        {
            "$addFields": {
                "durationDays": {
                    "$dateDiff": {
                        "startDate": "$start_date",
                        "endDate": "$end_date",
                        "unit": "day"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "project": "$name",
                "status": 1,
                "startDate": "$start_date",
                "endDate": "$end_date",
                "durationDays": 1,
                "value": "$revenue"
            }
        }
    ])

    timeline = await projects_collection.aggregate(pipeline).to_list(length=None)

    return timeline