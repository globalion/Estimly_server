from fastapi import APIRouter, Depends
from database.mongo import built_in_templates_collection
from utils.serializers import serialize_ids_only
from dependencies import get_current_user

router = APIRouter(
    prefix="/api/built-in-templates",
    tags=["Templates"]
)

@router.get("/")
async def get_builtin_templates(user=Depends(get_current_user)):
    """
    Global endpoint
    Returns all ACTIVE built-in templates
    """
    cursor = built_in_templates_collection.find(
        {"status": "active"},
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
    return [serialize_ids_only(t) for t in templates]
