import uuid
import enum
from sqlalchemy import Column, String, TIMESTAMP, Text, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin

class ContentTypeEnum(enum.Enum):
    PDF = "PDF"
    JSON = "JSON"
    MD = "MD"
    CSV = "CSV"

class ProjectOutput(Base, EncryptedModelMixin):
    __tablename__ = "project_output"

    _encrypted_fields = ['content','notes']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    project_step_id = Column(UUID(as_uuid=True), ForeignKey("project_step.id", ondelete="CASCADE"), nullable=False)
    content_type = Column(SAEnum(ContentTypeEnum), nullable=False)
    output_name = Column(String(255))
    content = Column(Text) # Encrypted
    notes = Column(Text) # Encrypted
    version_number = Column(Integer, nullable=False, default=1)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    project = relationship("Project", back_populates="outputs")
    project_step = relationship("ProjectStep", back_populates="output")