RESOURCE_RATES = {
    "junior_dev": 15,
    "senior_dev": 30,
    "tech_lead": 45,
    "ai_engineer": 50,
    "qa_junior": 12,
    "qa_senior": 22,
    "ui_ux": 25,
    "pm": 35,
    "devops": 32,
    "business_analyst": 28
}

COMPLEXITY_MULTIPLIERS = {
    "low": 1.0,
    "medium": 1.3,
    "high": 1.6,
    "extreme": 2.0
}

DEFAULT_SETTINGS = {
    # Used in cost calculation
    "productivity_factor": 0.85,

    # Used in timeline calculation
    "sprint_duration_weeks": 2,
    "working_hours_per_day": 8,
    "working_days_per_week": 5
}
