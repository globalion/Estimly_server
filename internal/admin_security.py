from fastapi import Header, HTTPException

INTERNAL_ADMIN_KEY = "estimly-internal-admin-key"

def internal_admin_auth(x_internal_admin_key: str = Header(...)):
    if x_internal_admin_key != INTERNAL_ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
