def calculate_task_cost(task, resource_rates, settings):
    hours = task["hours"]
    role = task["role"]
    level = task["level"]

    if role not in resource_rates:
        raise ValueError(f"Hourly rate not found for role: {role}")

    hourly_rate = resource_rates[role]

    # Use DB complexity multipliers
    multiplier = settings["complexity_multipliers"].get(level, 1)

    adjusted_hours = hours * multiplier

    cost = (
        adjusted_hours
        * hourly_rate
        * settings["productivity_factor"]
    )

    return adjusted_hours, cost, role, hourly_rate


def calculate_estimation(project, resource_rates, settings):
    total_hours = 0
    total_cost = 0

    modules = []
    resource_hours = {}
    used_roles_snapshot = {}

    for module in project["modules"]:
        module_hours = 0
        module_cost = 0

        for feature in module["features"]:
            for task in feature["tasks"]:
                adj_hours, cost, role, hourly_rate = calculate_task_cost(
                    task,
                    resource_rates,
                    settings
                )

                module_hours += adj_hours
                module_cost += cost

                total_hours += adj_hours
                total_cost += cost

                resource_hours[role] = resource_hours.get(role, 0) + adj_hours
                used_roles_snapshot[role] = hourly_rate

        modules.append({
            "name": module["name"],
            "hours": round(module_hours, 1),
            "cost": round(module_cost)
        })

    # Pricing 
    risk_amount = total_cost * project["risk_buffer"] / 100
    cost_with_risk = total_cost + risk_amount

    margin_amount = cost_with_risk * project["target_margin"] / 100
    price_before_negotiation = cost_with_risk + margin_amount

    negotiation_amount = price_before_negotiation * project["negotiation_buffer"] / 100
    final_price = price_before_negotiation + negotiation_amount

    profit = final_price - total_cost
    profit_percent = (profit / total_cost * 100) if total_cost else 0

    
    # Timeline 
    hours_per_week = (
        settings["working_hours_per_day"]
        * settings["working_days_per_week"]
    )

    available_hours_per_week = (
        hours_per_week
        * project["estimated_team_size"]
        * 0.8
    )

    weeks_required = (total_hours / available_hours_per_week).__ceil__()

    sprints_required = (
        weeks_required
        / settings["sprint_duration_weeks"]
    ).__ceil__()

    
    # Resource Allocation 
    resource_allocation = [
        {
            "role": role,
            "hours": round(hrs, 1),
            "hourly_rate": used_roles_snapshot[role],
            "percentage": round((hrs / total_hours) * 100, 1)
        }
        for role, hrs in resource_hours.items()
    ]

    return {
        "totals": {
            "hours": round(total_hours, 1),
            "base_cost": round(total_cost)
        },

        "wbs": {
            "modules": modules
        },

        "pricing": {
            "risk_buffer_percent": project["risk_buffer"],
            "risk_buffer_amount": round(risk_amount),
            "cost_with_risk": round(cost_with_risk),

            "target_margin_percent": project["target_margin"],
            "margin_amount": round(margin_amount),

            "price_before_negotiation": round(price_before_negotiation),
            "negotiation_buffer_percent": project["negotiation_buffer"],
            "negotiation_buffer_amount": round(negotiation_amount),

            "final_price": round(final_price),
            "profit": round(profit),
            "profit_margin_percent": round(profit_percent, 1)
        },

        "timeline": {
            "weeks_required": weeks_required,
            "months_estimate": (weeks_required / 4).__ceil__(),
            "sprints_required": sprints_required,
            "estimated_team_size": project["estimated_team_size"],

            "assumptions": {
                "working_hours_per_day": settings["working_hours_per_day"],
                "working_days_per_week": settings["working_days_per_week"],
                "sprint_duration_weeks": settings["sprint_duration_weeks"],
                "resource_efficiency_percent": 80
            }
        },

        "resource_allocation": resource_allocation,
        "rate_snapshot": used_roles_snapshot
    }
