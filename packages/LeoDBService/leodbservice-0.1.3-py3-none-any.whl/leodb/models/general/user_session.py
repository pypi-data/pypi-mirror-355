import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, Text, CheckConstraint, Index, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin

class UserSession(Base, EncryptedModelMixin):
    """
    Manages user sessions.
    """
    __tablename__ = "user_sessions"

    _encrypted_fields = ['client_ip_address', 'user_agent']

    # Identifiers
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Token and authentication
    jwt_token_hash = Column(String(255), nullable=False, index=True)

    # Client Information
    client_type = Column(String(50), nullable=False)  # WEB, TEAMS, MOBILE, API, OTHER
    client_version = Column(String(50))
    client_ip_address = Column(String)  # ENCRYPTED
    user_agent = Column(Text)  # ENCRYPTED

    # Session Management
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    last_activity_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Metadata
    session_metadata = Column("metadata", JSON)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Constraints
    __table_args__ = (
        CheckConstraint("client_type IN ('WEB', 'TEAMS', 'MOBILE', 'API', 'OTHER')", name="user_sessions_client_type_check"),
        Index('idx_user_sessions_jwt_hash', 'jwt_token_hash'),
    )