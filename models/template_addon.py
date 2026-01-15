# import uuid
# from sqlalchemy import Column, String, Integer, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from database import Base

# class TemplateAddon(Base):
#     __tablename__ = "template_addons"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     template_id = Column(UUID, ForeignKey("project_templates.id"))
#     addon_name = Column(String, nullable=False)
#     extra_hours = Column(Integer, nullable=False)
