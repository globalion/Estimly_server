from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from database.mongo import (
    resource_roles_collection,
    resource_rate_history_collection
)
#from dependencies import get_current_user
from utils.normalize import normalize
from schemas.resource_role import (
    ResourceRoleCreate,
    ResourceRoleUpdate
)

from utils.permissions import require_permission
from utils.serializers import serialize_ids_only
from pymongo import ReturnDocument


router = APIRouter(
    prefix="/api/resource-roles",
    tags=["Resource Roles"]
)

# Create Custom role
@router.post("/")
async def create_custom_role(
    payload: ResourceRoleCreate,
    user=Depends(require_permission("roles.create"))
):
    
    role_name = normalize(payload.label)

    existing = await resource_roles_collection.find_one({
        "name": role_name,
        "is_active": True,
        "$or": [
            {"type": "default"},
            {"company_id": ObjectId(user["company_id"])}
        ]
    })

    if existing:
        raise HTTPException(409, "Role with this name already exists")

    now = datetime.utcnow()

    role_doc = {
        "name": role_name,
        "label": payload.label.strip(),
        "hourly_rate": payload.hourly_rate,
        "default_hourly_rate": payload.hourly_rate,
        "type": "custom",
        "company_id": ObjectId(user["company_id"]),
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }

    result = await resource_roles_collection.insert_one(role_doc)

    await resource_rate_history_collection.insert_one({
        "role_id": result.inserted_id,
        "role_name": role_name,
        "role_label": payload.label.strip(),
        "action": "added",
        "old_rate": 0,
        "new_rate": payload.hourly_rate,
        "change_percent": None,
        "company_id": ObjectId(user["company_id"]),
        "changed_by": ObjectId(user["_id"]),
        "changed_at": now
    })

    return {"message": "Custom role created successfully"}


# update role
@router.patch("/{role_id}")
async def update_resource_role(
    role_id: str,
    payload: ResourceRoleUpdate,
    user=Depends(require_permission("roles.update"))
):

    try:
        role_object_id = ObjectId(role_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid role ID")

    role = await resource_roles_collection.find_one({
        "_id": role_object_id,
        "$or": [
            {"type": "default"},
            {"company_id": ObjectId(user["company_id"])}
        ]
    })

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    now = datetime.utcnow()

    old_name = role["name"]
    old_label = role["label"]
    old_rate = role["hourly_rate"]

    updates = {}
    name_changed = False
    rate_changed = False

    # Prevent renaming default roles
    if role["type"] == "default" and payload.label:
        raise HTTPException(
            status_code=400,
            detail="Default role name cannot be changed"
        )

    
    # Handle Label Change
    if payload.label:
        new_label = payload.label.strip()

        if len(new_label) < 2:
            raise HTTPException(
                status_code=400,
                detail="Role name must be at least 2 characters"
            )

        if len(new_label) > 100:
            raise HTTPException(
                status_code=400,
                detail="Role name cannot exceed 100 characters"
            )

        new_name = normalize(new_label)

        if new_name != old_name:
            exists = await resource_roles_collection.find_one({
                "name": new_name,
                "is_active": True,
                "_id": {"$ne": role_object_id},
                "$or": [
                    {"type": "default"},
                    {"company_id": ObjectId(user["company_id"])}
                ]
            })

            if exists:
                raise HTTPException(
                    status_code=409,
                    detail="Role with this name already exists"
                )

            updates["name"] = new_name
            updates["label"] = new_label
            name_changed = True


    # Handle Rate Change
    if payload.hourly_rate is not None and payload.hourly_rate != old_rate:
        updates["hourly_rate"] = payload.hourly_rate
        rate_changed = True

    if not updates:
        return {"message": "No changes detected"}

    updates["updated_at"] = now

    final_label = updates.get("label", old_label)
    final_rate = updates.get("hourly_rate", old_rate)

    # History 
    history_entry = {
        "role_id": role["_id"],
        "role_name": old_name,
        "role_label": final_label,
        "action": "renamed" if name_changed else "updated",
        "old_rate": old_rate,
        "new_rate": final_rate,
        "change_percent": (
            round(((updates["hourly_rate"] - old_rate) / old_rate) * 100, 2)
            if rate_changed and old_rate
            else None
        ),
        "company_id": ObjectId(user["company_id"]),
        "changed_by": ObjectId(user["_id"]),
        "changed_at": now
    }

    if name_changed:
        history_entry["old_label"] = old_label
        history_entry["new_label"] = updates["label"]

    await resource_rate_history_collection.insert_one(history_entry)

    updated_role = await resource_roles_collection.find_one_and_update(
        {"_id": role_object_id},
        {"$set": updates},
        return_document=ReturnDocument.AFTER
    )

    return {
        "message": "Role updated successfully",
        "data": serialize_ids_only(updated_role)
    }



# Delete Custom role
@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    user=Depends(require_permission("roles.delete"))
):

    role = await resource_roles_collection.find_one({
        "_id": ObjectId(role_id),
        "company_id": ObjectId(user["company_id"])
    })

    if not role:
        raise HTTPException(404, "Role not found")

    if role["type"] == "default":
        raise HTTPException(400, "Default roles cannot be deleted")

    now = datetime.utcnow()

    await resource_rate_history_collection.insert_one({
        "role_id": role["_id"],
        "role_name": role["name"],
        "role_label": role["label"],
        "action": "deleted",
        "old_rate": role["hourly_rate"],
        "new_rate": None,
        "change_percent": None,
        "company_id": ObjectId(user["company_id"]),
        "changed_by": ObjectId(user["_id"]),
        "changed_at": now
    })

    await resource_roles_collection.delete_one({"_id": role["_id"]})

    return {"message": "Custom role deleted permanently"}


# Reset Default role
@router.post("/reset-defaults")
async def reset_default_roles(
    user=Depends(require_permission("roles.reset_defaults"))
):

    now = datetime.utcnow()

    default_roles = await resource_roles_collection.find(
        {"type": "default"}
    ).to_list(None)

    updated = []

    for role in default_roles:
        default_rate = role.get("default_hourly_rate")
        if role["hourly_rate"] == default_rate:
            continue

        old_rate = role["hourly_rate"]
        new_rate = default_rate

        await resource_rate_history_collection.insert_one({
            "role_id": role["_id"],
            "role_name": role["name"],
            "role_label": role["label"],
            "action": "reset",
            "old_rate": old_rate,
            "new_rate": new_rate,
            "change_percent": (
                round(((new_rate - old_rate) / old_rate) * 100, 2)
                if old_rate else 0
            ),
            "company_id": ObjectId(user["company_id"]),
            "changed_by": ObjectId(user["_id"]),
            "changed_at": now
        })

        await resource_roles_collection.update_one(
            {"_id": role["_id"]},
            {"$set": {"hourly_rate": new_rate, "updated_at": now}}
        )

        updated.append(role["label"])

    return {
        "message": "Default roles reset successfully",
        "updated_count": len(updated),
        "roles": updated
    }


# Get All roles
@router.get("/")
async def get_roles(
    user=Depends(require_permission("roles.read"))
):

    roles = await resource_roles_collection.find({
    "$or": [
        {"type": "default"},
        {"company_id": ObjectId(user["company_id"])}
    ],
    "is_active": True
}).to_list(None)


    role_ids = [r["_id"] for r in roles]

    history_counts = await resource_rate_history_collection.aggregate([
        {
            "$match": {
                "role_id": {"$in": role_ids},
                "company_id": ObjectId(user["company_id"])
            }
        },
        {"$group": {"_id": "$role_id", "count": {"$sum": 1}}}
    ]).to_list(None)

    history_map = {h["_id"]: h["count"] for h in history_counts}

    return [
        {
            "id": str(r["_id"]),
            "name": r["name"],
            "label": r["label"],
            "hourly_rate": r["hourly_rate"],
            "type": r["type"],
            "history_count": history_map.get(r["_id"], 0)
        }
        for r in roles
    ]

# Get all role history
@router.get("/history")
async def get_all_rate_history(
    user=Depends(require_permission("roles.history.read"))
):


    history = await resource_rate_history_collection.find({
    "company_id": ObjectId(user["company_id"])
}).sort("changed_at", -1).to_list(None)


    return [
        {
            "changed_at": h["changed_at"],
            "role_label": h["role_label"],
            "action": h["action"],
            "old_rate": h.get("old_rate"),
            "new_rate": h.get("new_rate"),
            "change_percent": h.get("change_percent"),
            "old_label": h.get("old_label"),
            "new_label": h.get("new_label")
        }
        for h in history
    ]


# Get single role
@router.get("/{role_id}")
async def get_role_id(
    role_id: str,
    user=Depends(require_permission("roles.read"))
):

    role = await resource_roles_collection.find_one({
        "_id": ObjectId(role_id),
        "$or": [
            {"type": "default"},
            {"company_id": ObjectId(user["company_id"])} 
        ]
    })

    if not role:
        raise HTTPException(404, "Role not found")

    history_count = await resource_rate_history_collection.count_documents({
        "role_id": role["_id"],
        "company_id": ObjectId(user["company_id"])
    })

    return {
        "id": str(role["_id"]),
        "name": role["name"],
        "label": role["label"],
        "hourly_rate": role["hourly_rate"],
        "type": role["type"],
        "history_count": history_count,
        "created_at": role.get("created_at"),
        "updated_at": role.get("updated_at")
    }


# Get single role history
@router.get("/{role_id}/history")
async def get_role_history(
    role_id: str,
    user=Depends(require_permission("roles.history.read"))
):

    history = await resource_rate_history_collection.find(
        {
  "role_id": ObjectId(role_id),
  "company_id": ObjectId(user["company_id"])
}).sort("changed_at", -1).to_list(None)

    return [
        {
            "changed_at": h["changed_at"],
            "role_label": h["role_label"],
            "action": h["action"],
            "old_rate": h.get("old_rate"),
            "new_rate": h.get("new_rate"),
            "change_percent": h.get("change_percent"),
            "old_label": h.get("old_label"),
            "new_label": h.get("new_label")
        }
        for h in history
    ]


