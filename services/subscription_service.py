from datetime import datetime, timedelta
from core.subscription_config import PLAN_DETAILS

def calculate_dates(plan, existing=None):

    now = datetime.utcnow()

    if existing and existing.get("end_date") and existing["end_date"] > now:
        start_date = existing["end_date"]
    else:
        start_date = now

    duration = PLAN_DETAILS[plan]["duration_days"]
    end_date = start_date + timedelta(days=duration)

    return start_date, end_date
