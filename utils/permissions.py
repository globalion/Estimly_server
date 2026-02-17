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
        "users.manage",
        "users.assign_roles",
        "company.settings.manage",
        "projects.view_all",
        "estimates.view_all"
    ],

    USER_ROLES["PROJECT_MANAGER"]: [
        "projects.create",
        "estimates.view_all",
        "estimates.review",
        "estimates.approve",
        "estimates.lock",
        "reports.view"
    ],

    USER_ROLES["ESTIMATOR"]: [
        "estimates.create",
        "estimates.edit_draft",
        "estimates.submit",
        "estimates.view_team"
    ],

    USER_ROLES["VIEWER"]: [
        "projects.view",
        "estimates.view",
        "reports.view"
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
