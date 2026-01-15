from bson import ObjectId

def serialize_project(project: dict) -> dict:
    if not project:
        return None

    return {
        "id": str(project["_id"]),
        "name": project["name"],
        "client_name": project["client_name"],
        "description": project.get("description"),
        "estimation_technique": project["estimation_technique"],
        "target_margin": project["target_margin"],
        "risk_buffer": project["risk_buffer"],
        "negotiation_buffer": project["negotiation_buffer"],
        "estimated_team_size": project["estimated_team_size"],
        "status": project["status"],
        "company_id": str(project["company_id"]),
        "created_by": str(project["created_by"]),
        "created_at": project["created_at"],
    }


def serialize_project_list(projects: list) -> list:
    return [serialize_project(p) for p in projects]
