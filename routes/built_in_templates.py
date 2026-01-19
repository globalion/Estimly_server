from fastapi import APIRouter, Depends
from bson import ObjectId

from database.mongo import built_in_templates_collection
from dependencies import get_current_user

router = APIRouter(
    prefix="/api/built_in_templates",
    tags=["Templates"]
)

@router.get("")
async def get_builtin_templates(user=Depends(get_current_user)):
    """
    Global endpoint
    Returns all ACTIVE built-in templates
    """
    cursor = built_in_templates_collection.find(
        {
            "status": "active"  # filter
        },
        {
            "_id": 1,
            "name": 1,
            "description": 1,
            "default_margin": 1,
            "risk_buffer": 1,
            "modules": 1,
            "addons": 1,
        }
    )

    templates = await cursor.to_list(length=None)

    for t in templates:
        t["id"] = str(t.pop("_id"))

    return {
        "templates": templates
    }
