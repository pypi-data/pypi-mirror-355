import enum
import uuid
from sqlalchemy import (
    Column, String, ForeignKey, Enum as SAEnum, DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin

class InvitationStatusEnum(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class UserInvitation(Base, EncryptedModelMixin):
    __tablename__ = "user_invitations"

    _encrypted_fields = ['invited_user_email']

    invitation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)

    invited_user_email = Column(String, nullable=False, index=True) # Encrypted
    invited_user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)

    token_hash = Column(String(255), nullable=False, unique=True)
    status = Column(SAEnum(InvitationStatusEnum, name="invitation_status_enum", create_type=False), nullable=False, default=InvitationStatusEnum.PENDING)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # --- Relationships ---
    inviting_admin = relationship("User", foreign_keys=[invited_by_user_id], back_populates="sent_invitations")
    account = relationship("Account", back_populates="invitations")
    invited_user = relationship("User", foreign_keys=[invited_user_id], back_populates="received_invitation")