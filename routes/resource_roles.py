from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from database.mongo import (
    resource_roles_collection,
    resource_rate_history_collection
)
from dependencies import get_current_user
from utils.normalize import normalize_role_name
from schemas.resource_role import (
    ResourceRoleCreate,
    ResourceRoleUpdate
)

router = APIRouter(
    prefix="/api/resource-roles",
    tags=["Resource Roles"]
)

# Create Custom role
@router.post("/")
async def create_custom_role(
    payload: ResourceRoleCreate,
    user=Depends(get_current_user)
):
    role_name = normalize_role_name(payload.label)

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


# Update Role
@router.patch("/{role_id}")
async def update_resource_role(
    role_id: str,
    payload: ResourceRoleUpdate,
    user=Depends(get_current_user)
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

    now = datetime.utcnow()

    old_name = role["name"]
    old_label = role["label"]
    old_rate = role["hourly_rate"]

    new_name = old_name
    new_label = old_label
    new_rate = old_rate

    updates = {}
    name_changed = False
    rate_changed = False

    if role["type"] == "default":
        if payload.label:
            raise HTTPException(
                status_code=400,
                detail="Default role name cannot be changed"
            )

    if payload.label:
        new_label = payload.label.strip()
        new_name = normalize_role_name(new_label)

        if new_name != old_name:
            exists = await resource_roles_collection.find_one({
                "name": new_name,
                "is_active": True,
                "_id": {"$ne": ObjectId(role_id)},
                "$or": [
                    {"type": "default"},
                    {"company_id": ObjectId(user["company_id"])}
                ]
            })

            if exists:
                raise HTTPException(409, "Role with this name already exists")

            updates["name"] = new_name
            updates["label"] = new_label
            name_changed = True

    if payload.hourly_rate is not None and payload.hourly_rate != old_rate:
        new_rate = payload.hourly_rate
        updates["hourly_rate"] = new_rate
        rate_changed = True

    if not updates:
        return {"message": "No changes detected"}

    updates["updated_at"] = now

    action = "renamed" if name_changed else "updated"
        
    history_entry = {
        "role_id": role["_id"],
        "role_name": old_name,     
        "role_label": (
        new_label if name_changed else old_label
    ),        
        "action": action,
        "old_rate": old_rate,
        "new_rate": new_rate,
        "change_percent": None,
        "company_id": ObjectId(user["company_id"]),
        "changed_by": ObjectId(user["_id"]),
        "changed_at": now
    }

    if rate_changed:
        history_entry["old_rate"] = old_rate
        history_entry["new_rate"] = new_rate
        history_entry["change_percent"] = round(
        ((new_rate - old_rate) / old_rate) * 100, 2
    ) if old_rate else 0

    if name_changed:
        history_entry["old_label"] = old_label
        history_entry["new_label"] = new_label

    await resource_rate_history_collection.insert_one(history_entry)

    await resource_roles_collection.update_one(
        {"_id": role["_id"]},
        {"$set": updates}
    )

    return {"message": "Role updated successfully", "action": action}


# Delete Custom role
@router.delete("/{role_id}")
async def delete_role(role_id: str, user=Depends(get_current_user)):
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
async def reset_default_roles(user=Depends(get_current_user)):
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
async def get_roles(user=Depends(get_current_user)):

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
async def get_all_rate_history(user=Depends(get_current_user)):

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
async def get_role_id(role_id: str, user=Depends(get_current_user)):
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
async def get_role_history(role_id: str, user=Depends(get_current_user)):
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


