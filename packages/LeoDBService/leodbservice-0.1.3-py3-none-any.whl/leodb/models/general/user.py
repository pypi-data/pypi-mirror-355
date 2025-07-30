import enum
import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, Text, Index, Enum as SAEnum, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin
# Import UserInvitation directly to resolve relationship strings
from .user_invitation import UserInvitation

class UserStatusEnum(enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING_TEAM_INVITATION = "PENDING_TEAM_INVITATION"
    INACTIVE = "INACTIVE"

class User(Base, EncryptedModelMixin):
    """
    Represents the main user table, storing primary information.
    """
    __tablename__ = "users"

    _encrypted_fields = [
        'email', 'display_name', 'given_name', 'family_name',
        'preferred_username', 'config_delegated_to_name',
        'config_delegated_to_email', 'metadata'
    ]

    # Identifiers
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entra_id = Column(String(255), unique=True, nullable=False, index=True)
    tenant_id = Column(String(255), index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)

    # Personal Information (ENCRYPTED)
    email = Column(String)
    display_name = Column(String)
    given_name = Column(String)
    family_name = Column(String)
    preferred_username = Column(String)

    # Configuration Delegation (ENCRYPTED)
    config_delegated_to_name = Column(String)
    config_delegated_to_email = Column(String)

    # Status and Permissions
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    is_team_admin = Column(Boolean, nullable=False, default=False, index=True)
    status = Column(SAEnum(UserStatusEnum, name="user_status_enum", create_type=False), nullable=False, default=UserStatusEnum.PENDING_TEAM_INVITATION, index=True)
    user_metadata = Column("metadata", JSON)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    last_login_at = Column(TIMESTAMP(timezone=True), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    account = relationship("Account", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    themes = relationship("UserTheme", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("UserInvitation", foreign_keys=[UserInvitation.invited_by_user_id], back_populates="inviting_admin", cascade="all, delete-orphan")
    received_invitation = relationship("UserInvitation", foreign_keys=[UserInvitation.invited_user_id], back_populates="invited_user", uselist=False, cascade="all, delete-orphan")

# Additional Indexes
Index('idx_users_last_login', User.last_login_at)