"""
Modèles SQLAlchemy pour les scratchpads.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..base import Base

class Scratchpad(Base):
    __tablename__ = "scratchpads"
    _encrypted_fields = ['content']

    __table_args__ = (
        Index("ix_scratchpads_conversation_id", "conversation_id"),
        Index("ix_scratchpads_expires_at", "expires_at"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False
    )
    content = Column(JSON, nullable=False) # Encrypted field
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Relation
    conversation = relationship("Conversation", back_populates="scratchpads")