# from pydantic import BaseModel
# from typing import List, Optional
# from uuid import UUID

# class TemplateModuleSchema(BaseModel):
#     module_name: str

# class TemplateAddonSchema(BaseModel):
#     addon_name: str
#     extra_hours: int

# class TemplateCreate(BaseModel):
#     name: str
#     description: Optional[str]
#     default_margin: float
#     risk_buffer: float
#     modules: List[TemplateModuleSchema]
#     addons: List[TemplateAddonSchema] = []

# class TemplateResponse(BaseModel):
#     id: UUID
#     name: str
#     description: Optional[str]
#     default_margin: float
#     risk_buffer: float
#     is_builtin: bool
#     modules: List[TemplateModuleSchema]
#     addons: List[TemplateAddonSchema]

#     class Config:
#         from_attributes = True
