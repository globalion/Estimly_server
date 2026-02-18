from fastapi import Depends, HTTPException
from dependencies import get_current_user


USER_ROLES = {
    "OWNER": "owner",
    "ADMIN": "admin",
    "PROJECT_MANAGER": "project_manager",
    "ESTIMATOR": "estimator",
    "VIEWER": "viewer"
}
    

ROLE_PERMISSIONS = {

    USER_ROLES["OWNER"]: ["*"],

    USER_ROLES["ADMIN"]: [
        "users.invite",
        "company.settings.update",

        "projects.create",
        "projects.read",
        "projects.update",
        "projects.delete",
        "projects.change_status",

        "templates.create",
        "templates.read",
        "templates.update",
        "templates.delete",

        "roles.create",
        "roles.read",
        "roles.update",
        "roles.delete",
        "roles.reset_defaults",
        "roles.history.read"
    ],

    USER_ROLES["PROJECT_MANAGER"]: [
        "projects.create",
        "projects.read",
        "projects.update",
        "projects.change_status",

        "templates.create",
        "templates.read",
        "templates.update",

        "roles.read",
        "roles.history.read"
    ],

    USER_ROLES["ESTIMATOR"]: [
        "projects.create",
        "projects.read",
        "projects.update",

        "templates.read",
        "roles.read"
    ],

    USER_ROLES["VIEWER"]: [
        "projects.read",
        "templates.read",
        "roles.read"
    ]
}



def require_permission(permission: str):

    def checker(current_user=Depends(get_current_user)):

        role = current_user.get("role")

        if not role:
            raise HTTPException(
                status_code=403,
                detail="Role information missing"
            )

        permissions = ROLE_PERMISSIONS.get(role)

        if not permissions:
            raise HTTPException(
                status_code=403,
                detail="User role is not recognized"
            )

        # Owner full access
        if "*" in permissions:
            return current_user

        if permission not in permissions:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return checker
