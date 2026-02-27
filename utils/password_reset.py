from datetime import datetime, timedelta
from jose import jwt
from decouple import config

SECRET_KEY = config("PW_RESET_SECRET_KEY")
ALGORITHM = "HS256"
RESET_TOKEN_EXPIRE_MINUTES = 30

def create_reset_token(email: str):
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None
