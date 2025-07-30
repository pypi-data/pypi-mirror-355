import uuid
import enum
from sqlalchemy import Column, String, TIMESTAMP, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from .project_step_data_source_association import project_step_data_source_association
from .project_step_tool_association import project_step_tool_association

class ProjectStepStatusEnum(enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ProjectStep(Base):
    __tablename__ = "project_step"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    prompt = Column(Text)
    output_name = Column(String(255))
    status = Column(SAEnum(ProjectStepStatusEnum), nullable=False, default=ProjectStepStatusEnum.PLANNED)
    notes = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    project = relationship("Project", back_populates="project_steps")
    output = relationship("ProjectOutput", back_populates="project_step", uselist=False, cascade="all, delete-orphan")
    
    data_sources = relationship("DataSource", secondary=project_step_data_source_association)
    tools = relationship("ToolUseSpec", secondary=project_step_tool_association)