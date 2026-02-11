from bson import ObjectId
from database.mongo import resource_roles_collection

async def get_resource_rate_map(company_id):
    rate_map = {}

    # System default roles
    default_cursor = resource_roles_collection.find(
        {"type": "default", "is_active": True},
        {"name": 1, "hourly_rate": 1}
    )

    async for role in default_cursor:
        rate_map[role["name"]] = role["hourly_rate"]

    # Company custom roles (override defaults)
    custom_cursor = resource_roles_collection.find(
        {
            "type": "custom",
            "company_id": ObjectId(company_id),
            "is_active": True
        },
        {"name": 1, "hourly_rate": 1}
    )

    async for role in custom_cursor:
        rate_map[role["name"]] = role["hourly_rate"]

    return rate_map
