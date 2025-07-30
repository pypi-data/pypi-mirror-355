"""
Modèles SQLAlchemy pour le contexte de conversation.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..base import Base

class ConversationContext(Base):
    __tablename__ = "conversation_context"
    
    context_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False)
    instruction_ids = Column(JSON, nullable=True)
    document_types = Column(JSON, nullable=True)
    summary = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    conversation = relationship("Conversation", back_populates="contexts")