# import uuid
# from sqlalchemy import Column, String, ForeignKey
# from sqlalchemy.dialects.postgresql import UUID
# from database import Base

# class TemplateModule(Base):
#     __tablename__ = "template_modules"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     template_id = Column(UUID, ForeignKey("project_templates.id"))
#     module_name = Column(String, nullable=False)
