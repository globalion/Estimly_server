"""from datetime import datetime
from database.mongo import (
    estimation_techniques_collection,
    estimation_technique_info_collection,
    estimation_settings_collection
)

ESTIMATION_TECHNIQUES = {
    "WBS": "wbs",
    "BOTTOM_UP": "bottom_up",
    "ANALOGOUS": "analogous",
    "THREE_POINT": "three_point",
    "AGILE": "agile",
    "COCOMO": "cocomo",
    "FUNCTION_POINT": "function_point",
    "USE_CASE_POINT": "use_case_point",
    "WIDEBAND_DELPHI": "wideband_delphi",
    "PARAMETRIC": "parametric",
    "EXPERT_JUDGMENT": "expert_judgment",
    "EVM": "evm",
    "MONTE_CARLO": "monte_carlo"
}

async def seed():
    for code, key in ESTIMATION_TECHNIQUES.items():
        await estimation_techniques_collection.update_one(
            {"key": key},
            {"$setOnInsert": {
                "key": key,
                "code": code,
                "created_at": datetime.utcnow()
            }},
            upsert=True
        )

    await estimation_settings_collection.update_one(
        {},
        {"$set": {
            "default_margin_percent": 30,
            "default_risk_buffer": 15,
            "default_negotiation_buffer": 10,
            "productivity_factor": 0.85,
            "sprint_duration_weeks": 2,
            "working_hours_per_day": 8,
            "working_days_per_week": 5,
            "default_estimation_technique": "wbs"
        }},
        upsert=True
    )
"""""
import asyncio
from database.mongo import (
    estimation_techniques_collection,
    estimation_technique_info_collection,
    estimation_settings_collection
)

# ---- JS -> PYTHON DATA ----

ESTIMATION_TECHNIQUES = {
    "WBS": "wbs",
    "BOTTOM_UP": "bottom_up",
    "ANALOGOUS": "analogous",
    "THREE_POINT": "three_point",
    "AGILE": "agile",
    "COCOMO": "cocomo",
    "FUNCTION_POINT": "function_point",
    "USE_CASE_POINT": "use_case_point",
    "WIDEBAND_DELPHI": "wideband_delphi",
    "PARAMETRIC": "parametric",
    "EXPERT_JUDGMENT": "expert_judgment",
    "EVM": "evm",
    "MONTE_CARLO": "monte_carlo"
}

ESTIMATION_TECHNIQUE_INFO = {
    "wbs": {
        "name": "Work Breakdown Structure (WBS)",
        "standard": "PMBOK / PMI",
        "description": "Hierarchical decomposition of project into smaller components for detailed estimation",
        "use_cases": "Complex projects, detailed planning, scope management",
        "complexity": "Medium",
        "time_required": "Medium",
        "accuracy": "High"
    },
    "bottom_up": {
        "name": "Bottom-Up Estimation",
        "standard": "Industry Standard",
        "description": "Estimate individual tasks and roll up to get total project estimate",
        "use_cases": "Detailed projects, known requirements, experienced teams",
        "complexity": "Medium",
        "time_required": "High",
        "accuracy": "Very High"
    },
    "analogous": {
        "name": "Analogous (Comparative) Estimation",
        "standard": "PMBOK",
        "description": "Use historical data from similar projects to estimate current project",
        "use_cases": "Early project phases, limited information, quick estimates",
        "complexity": "Low",
        "time_required": "Low",
        "accuracy": "Medium"
    },
    "three_point": {
        "name": "Three-Point Estimation (PERT)",
        "standard": "PERT",
        "description": "Calculate weighted average using optimistic, pessimistic, and most likely estimates",
        "use_cases": "Uncertain projects, risk assessment, range-based estimates",
        "complexity": "Medium",
        "time_required": "Medium",
        "accuracy": "High"
    },
    "agile": {
        "name": "Agile Estimation (Story Points & Velocity)",
        "standard": "Scrum / Agile",
        "description": "Use story points, velocity, and sprint-based planning for estimation",
        "use_cases": "Agile projects, iterative development, flexible scope",
        "complexity": "Medium",
        "time_required": "Low",
        "accuracy": "Medium"
    },
    "cocomo": {
        "name": "COCOMO (Constructive Cost Model)",
        "standard": "Barry Boehm",
        "description": "Algorithmic cost model based on lines of code and complexity factors",
        "use_cases": "Software development, effort prediction, large projects",
        "complexity": "High",
        "time_required": "Medium",
        "accuracy": "High"
    },
    "function_point": {
        "name": "Function Point Analysis (FPA)",
        "standard": "IFPUG",
        "description": "Estimate based on functional requirements and system characteristics",
        "use_cases": "Business applications, requirement-based estimation, language-independent",
        "complexity": "High",
        "time_required": "High",
        "accuracy": "High"
    },
    "use_case_point": {
        "name": "Use Case Point (UCP) Estimation",
        "standard": "Gustav Karner",
        "description": "Estimate based on use cases, actors, and technical complexity factors",
        "use_cases": "Object-oriented systems, use case-driven development",
        "complexity": "Medium",
        "time_required": "Medium",
        "accuracy": "Medium"
    },
    "wideband_delphi": {
        "name": "Wideband Delphi Technique",
        "standard": "RAND Corporation",
        "description": "Consensus-based estimation using expert opinions and iterative refinement",
        "use_cases": "Expert teams, uncertain requirements, collaborative estimation",
        "complexity": "Low",
        "time_required": "Medium",
        "accuracy": "Medium"
    },
    "parametric": {
        "name": "Parametric Estimation",
        "standard": "PMBOK",
        "description": "Use statistical relationships and historical data to calculate estimates",
        "use_cases": "Repetitive projects, statistical data available, quick estimates",
        "complexity": "Medium",
        "time_required": "Low",
        "accuracy": "High"
    },
    "expert_judgment": {
        "name": "Expert Judgment-Based Estimation",
        "standard": "Industry Practice",
        "description": "Leverage experience and knowledge of experts for estimation",
        "use_cases": "Specialized projects, domain expertise required, quick validation",
        "complexity": "Low",
        "time_required": "Low",
        "accuracy": "Medium"
    },
    "evm": {
        "name": "Earned Value Management (EVM)-informed Estimation",
        "standard": "PMI / ANSI",
        "description": "Use earned value metrics to refine and update project estimates",
        "use_cases": "Ongoing projects, progress tracking, forecast adjustments",
        "complexity": "High",
        "time_required": "Medium",
        "accuracy": "High"
    },
    "monte_carlo": {
        "name": "Monte Carlo Simulation (Risk-based)",
        "standard": "Statistical Method",
        "description": "Probabilistic analysis using multiple simulations to model uncertainty",
        "use_cases": "High uncertainty, risk analysis, range-based forecasts",
        "complexity": "Very High",
        "time_required": "High",
        "accuracy": "Very High"
    }
}

DEFAULT_SETTINGS = {
    "default_margin_percent": 30,
    "default_risk_buffer": 15,
    "default_negotiation_buffer": 10,
    "productivity_factor": 0.85,
    "sprint_duration_weeks": 2,
    "working_hours_per_day": 8,
    "working_days_per_week": 5,
    "default_estimation_technique": "wbs"
}

# ---- SEED FUNCTION ----

async def seed_all():
    # Techniques
    for code, key in ESTIMATION_TECHNIQUES.items():
        await estimation_techniques_collection.update_one(
            {"key": key},
            {"$set": {"key": key, "code": code}},
            upsert=True
        )

    # Technique Info
    for key, info in ESTIMATION_TECHNIQUE_INFO.items():
        await estimation_technique_info_collection.update_one(
            {"technique_key": key},
            {"$set": {"technique_key": key, **info}},
            upsert=True
        )

    # Settings (single document)
    await estimation_settings_collection.update_one(
        {},
        {"$set": DEFAULT_SETTINGS},
        upsert=True
    )

    print("✅ Estimation data seeded successfully")

asyncio.run(seed_all())