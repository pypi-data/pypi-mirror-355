import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, ForeignKey, CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin

class UserPreferences(Base, EncryptedModelMixin):
    """
    Stores custom user preferences.
    """
    __tablename__ = "user_preferences"

    _encrypted_fields = [
        'leo_call_name', 'notification_email', 'notification_phone'
    ]

    # Identifiers
    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Interface Preferences
    language = Column(String(5), nullable=False, default='fr')

    # Leo Agent Preferences (ENCRYPTED)
    leo_call_name = Column(String)
    agent_tone = Column(String(20), nullable=False, default='professional')

    # Financial Preferences
    default_currency = Column(String(3), nullable=False, default='USD')

    # Notification Preferences (partially ENCRYPTED)
    notification_email_enabled = Column(Boolean, nullable=False, default=True)
    notification_sms_enabled = Column(Boolean, nullable=False, default=False)
    notification_email = Column(String)
    notification_phone = Column(String)

    # Flexible custom settings
    custom_settings = Column(JSON)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="preferences")

    # Constraints
    __table_args__ = (
        CheckConstraint("language IN ('fr', 'en')", name="user_preferences_language_check"),
        CheckConstraint("agent_tone IN ('friendly', 'professional', 'direct')", name="user_preferences_agent_tone_check"),
    )