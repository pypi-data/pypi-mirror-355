import uuid
import enum
from sqlalchemy import Column, String, TIMESTAMP, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base

class ProjectStatusEnum(enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Project(Base):
    __tablename__ = "project"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("record.id", ondelete="CASCADE"), nullable=False)
    prompt = Column(Text)
    conversation_history = Column(Text)
    status = Column(SAEnum(ProjectStatusEnum), nullable=False, default=ProjectStatusEnum.PLANNED)
    notes = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    record = relationship("Record", back_populates="projects")
    project_steps = relationship("ProjectStep", back_populates="project", cascade="all, delete-orphan")
    outputs = relationship("ProjectOutput", back_populates="project", cascade="all, delete-orphan")