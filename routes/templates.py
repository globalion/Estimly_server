from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.project_template import ProjectTemplate
from models.template_module import TemplateModule
from models.template_addon import TemplateAddon
from schemas.template import TemplateCreate, TemplateResponse
from dependencies import get_current_user

router = APIRouter(prefix="/templates", tags=["Templates"])

@router.get("/", response_model=List[TemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    return db.query(ProjectTemplate).filter(
        (ProjectTemplate.is_builtin == True) |
        (ProjectTemplate.company_id == user.company_id)
    ).all()

@router.post("/", response_model=TemplateResponse)
def create_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    template = ProjectTemplate(
        name=payload.name,
        description=payload.description,
        default_margin=payload.default_margin,
        risk_buffer=payload.risk_buffer,
        company_id=user.company_id,
        created_by=user.id,
        is_builtin=False
    )

    template.modules = [
        TemplateModule(module_name=m.module_name)
        for m in payload.modules
    ]

    template.addons = [
        TemplateAddon(addon_name=a.addon_name, extra_hours=a.extra_hours)
        for a in payload.addons
    ]

    db.add(template)
    db.commit()
    db.refresh(template)
    return template
