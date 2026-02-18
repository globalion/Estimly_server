from datetime import timedelta

PLAN_DETAILS = {
    "free": {
        "price": 0,
        "projects": 3,
        "users": 1,
        "ai_limit": 5,
        "duration_days": 365
    },
    "starter": {
        "price": 49.00,
        "projects": 25,
        "users": 5,
        "ai_limit": 50,
        "duration_days": 30
    },
    "professional": {
        "price": 149.00,
        "projects": -1,  # unlimited
        "users": 25,
        "ai_limit": 200,
        "duration_days": 30
    }
}
