from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from database.mongo import (
    resource_roles_collection,
    resource_rate_history_collection
)
from dependencies import get_current_user
from utils.serializers import serialize_ids_only
from utils.normalize import normalize_role_name
from schemas.resource_role import (
    ResourceRoleCreate,
    ResourceRoleUpdate
)

from pymongo import ReturnDocument

router = APIRouter(
    prefix="/api/resource-roles",
    tags=["Resource Roles"]
)
 
 
#create custom role
@router.post("/")
async def create_custom_role(
    payload: ResourceRoleCreate,
    user=Depends(get_current_user)
):
    # Generate canonical name
    role_name = normalize_role_name(payload.label)

    # Duplicate check
    existing = await resource_roles_collection.find_one({
        "name": role_name,
        "is_active": True
    })

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Role with this name already exists"
        )

    now = datetime.utcnow()

    # Create role
    role_doc = {
        "name": role_name,                 
        "label": payload.label.strip(),    
        "hourly_rate": payload.hourly_rate,
        "default_hourly_rate": payload.hourly_rate,
        "type": "custom",
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }

    result = await resource_roles_collection.insert_one(role_doc)

    # Insert rate history
    await resource_rate_history_collection.insert_one({
        "role_id": result.inserted_id,
        "role_name": role_name,
        "action": "added",
        "old_rate": 0,
        "new_rate": payload.hourly_rate,
        "change_percent": None,
        "changed_by": ObjectId(user["_id"]),
        "changed_at": now
    })

    return {
        "message": "Custom role created successfully",
        "role_name": role_name
    }


#update role data
@router.patch("/{role_id}")
async def update_resource_role(
    role_id: str,
    payload: ResourceRoleUpdate,
    user=Depends(get_current_user)
):
    role = await resource_roles_collection.find_one({
        "_id": ObjectId(role_id)
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

    if payload.label:
        new_label = payload.label.strip()
        new_name = normalize_role_name(new_label)

        if new_name != old_name:
            existing = await resource_roles_collection.find_one({
                "name": new_name,
                "is_active": True,
                "_id": {"$ne": ObjectId(role_id)}
            })
            if existing:
                raise HTTPException(409, "Role with this name already exists")

            updates["name"] = new_name
            updates["label"] = new_label
            name_changed = True


    if payload.hourly_rate is not None and payload.hourly_rate != old_rate:
        new_rate = payload.hourly_rate
        updates["hourly_rate"] = new_rate
        rate_changed = True

    if not updates:
        raise HTTPException(400, "No valid fields to update")

    updates["updated_at"] = now

    if name_changed:
        action = "renamed"
    elif rate_changed:
        action = "updated"
    else:
        action = "updated"

    history_entry = {
        "role_id": role["_id"],
        "role_name": old_name, 
        "action": action,
        "changed_by": ObjectId(user["_id"]),
        "changed_at": now
    }

    if rate_changed:
        history_entry["old_rate"] = old_rate
        history_entry["new_rate"] = new_rate
        history_entry["change_percent"] = round(
            ((new_rate - old_rate) / old_rate) * 100, 2
        ) if old_rate else None

    if name_changed:
        history_entry["old_name"] = old_name
        history_entry["new_name"] = new_name

    await resource_rate_history_collection.insert_one(history_entry)

    await resource_roles_collection.update_one(
        {"_id": role["_id"]},
        {"$set": updates}
    )

    return {
        "message": "Role updated successfully",
        "action": action
    }


#delete custom role  
@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    user=Depends(get_current_user)
):
    role = await resource_roles_collection.find_one({
        "_id": ObjectId(role_id)
    })
    if not role:
        raise HTTPException(404, "Role not found")
    

    if role["type"] == "default":
        raise HTTPException(
            status_code=400,
            detail="Default roles cannot be deleted"
        )

    now = datetime.utcnow()

    await resource_rate_history_collection.insert_one({
        "role_id": role["_id"],
        "role_name": role["name"],
        "action": "deleted",
        "old_rate": role["hourly_rate"],
        "new_rate": None,
        "old_label": role["label"],
        "new_label": role["label"],
        "change_percent": None,
        "changed_by": ObjectId(user["_id"]),
        "changed_at": now
    })

    await resource_roles_collection.delete_one({
        "_id": role["_id"]
    })

    return {"message": "Custom Role deleted permanently"}


#reset to default rate
@router.post("/reset-defaults")
async def reset_default_roles(
    user=Depends(get_current_user)
):
    now = datetime.utcnow()

    default_roles = await resource_roles_collection.find({
        "type": "default"
    }).to_list(None)

    updated = []

    for role in default_roles:
        default_rate = role.get("default_hourly_rate")
        if default_rate is None:
            continue

        if role["hourly_rate"] == default_rate:
            continue

        old_rate = role["hourly_rate"]
        new_rate = default_rate

        await resource_rate_history_collection.insert_one({
            "role_id": role["_id"],
            "action": "reset",
            "old_rate": old_rate,
            "new_rate": new_rate,
            "old_label": role["label"],
            "new_label": role["label"],
            "change_percent": round(
                ((new_rate - old_rate) / old_rate) * 100, 2
            ) if old_rate else None,
            "changed_by": ObjectId(user["_id"]),
            "changed_at": now
        })

        await resource_roles_collection.update_one(
            {"_id": role["_id"]},
            {"$set": {"hourly_rate": new_rate, "updated_at": now}}
        )

        updated.append(role["label"])

    return {
        "message": "Default roles reset",
        "updated_count": len(updated),
        "roles": updated
    }


# get all role data
@router.get("/")
async def get_roles():
    roles = await resource_roles_collection.find({}).to_list(None)

    role_ids = [r["_id"] for r in roles]

    history_counts = await resource_rate_history_collection.aggregate([
        {"$match": {"role_id": {"$in": role_ids}}},
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


# all role history
@router.get("/history")
async def get_all_rate_history(user=Depends(get_current_user)):
    history = await resource_rate_history_collection.find(
        {}
    ).sort("changed_at", -1).to_list(None)

    return [
        {
            "changed_at": h["changed_at"],
            "role_name": h["role_name"],
            "action": h["action"],

            # optional fields (safe access)
            "old_rate": h.get("old_rate"),
            "new_rate": h.get("new_rate"),
            "change_percent": h.get("change_percent"),

            "old_name": h.get("old_name"),
            "new_name": h.get("new_name"),
        }
        for h in history
    ]

#get single role data
@router.get("/{role_id}")
async def get_role_id(
    role_id: str,
    user=Depends(get_current_user)
):
    try:
        role_object_id = ObjectId(role_id)
    except Exception:
        raise HTTPException(400, "Invalid role id")

    role = await resource_roles_collection.find_one({
        "_id": role_object_id
    })

    if not role:
        raise HTTPException(404, "Role not found")

    history_count = await resource_rate_history_collection.count_documents({
        "role_id": role_object_id
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


#get single role history
@router.get("/{role_id}/history")
async def get_role_history(
    role_id: str,
    user=Depends(get_current_user)
):
    try:
        role_object_id = ObjectId(role_id)
    except Exception:
        raise HTTPException(400, "Invalid role id")

    history = await resource_rate_history_collection.find(
        {"role_id": role_object_id}
    ).sort("changed_at", -1).to_list(None)

    return [
        {
            "changed_at": h["changed_at"],
            "action": h["action"],
            "old_rate": h.get("old_rate"),
            "new_rate": h.get("new_rate"),
            "change_percent": h.get("change_percent"),
            "old_name": h.get("old_name"),
            "new_name": h.get("new_name")
        }
        for h in history
    ]
