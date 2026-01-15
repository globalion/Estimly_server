# import uuid
# from sqlalchemy import Column, String, Float, Boolean
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import relationship
# from database import Base

# class ProjectTemplate(Base):
#     __tablename__ = "project_templates"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     name = Column(String, nullable=False)
#     description = Column(String)
#     default_margin = Column(Float, nullable=False)
#     risk_buffer = Column(Float, nullable=False)
#     is_builtin = Column(Boolean, default=False)

#     company_id = Column(UUID, nullable=True)
#     created_by = Column(UUID, nullable=True)

#     modules = relationship("TemplateModule", cascade="all, delete-orphan")
#     addons = relationship("TemplateAddon", cascade="all, delete-orphan")
