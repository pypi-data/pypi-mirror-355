import uuid
from sqlalchemy import Column, String, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin
from .data_source_record import data_source_record

class Record(Base, EncryptedModelMixin):
    __tablename__ = "record"

    _encrypted_fields = ['title', 'description', 'record_data_entries', 'record_base_data']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True) # No FK constraint
    conversation_id = Column(UUID(as_uuid=True), index=True)
    title = Column(Text) 
    description = Column(Text) # Encrypted
    record_data_entries = Column(Text) # Encrypted
    record_base_data = Column(Text) # Encrypted

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    projects = relationship("Project", back_populates="record", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", secondary=data_source_record)