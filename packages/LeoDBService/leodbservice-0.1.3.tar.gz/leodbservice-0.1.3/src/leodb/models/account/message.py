"""
Modèles SQLAlchemy pour les messages des conversations 
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..base import Base

class Message(Base):
    __tablename__ = "messages"
    _encrypted_fields = ['content']
    
    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(String, nullable=False) # Encrypted field
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=True)
    
    # Relation
    conversation = relationship("Conversation", back_populates="messages")