from datetime import timedelta

PLAN_DETAILS = {
    "free": {
        "price": 0,
        "projects": 3,
        "users": 1,
        "ai_limit": 5,
        "duration_days": 3650
    },
    "starter": {
        "price": 4900,
        "projects": 25,
        "users": 5,
        "ai_limit": 50,
        "duration_days": 30
    },
    "professional": {
        "price": 14900,
        "projects": -1,  # unlimited
        "users": 25,
        "ai_limit": 200,
        "duration_days": 30
    }
}
