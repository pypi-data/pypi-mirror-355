import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .account_data_connection import AccountDataConnection
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin

class Account(Base, EncryptedModelMixin):
    """
    Represents a user or team account, grouping users, packages, and billing.
    """
    __tablename__ = "accounts"

    _encrypted_fields = ['config_admin_email']

    # Identifiers
    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Account Information
    account_name = Column(String(255))  # Optional company/account name
    
    # Account Type
    is_team = Column(Boolean, nullable=False, default=False, index=True)
    
    # Technical admin email (encrypted)
    config_admin_email = Column(String)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Relationships
    users = relationship("User", back_populates="account", cascade="all, delete-orphan")
    packages = relationship("Package", back_populates="account", cascade="all, delete-orphan")
    payment_methods = relationship("PaymentMethod", back_populates="account", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="account", cascade="all, delete-orphan")
    invitations = relationship("UserInvitation", back_populates="account", cascade="all, delete-orphan")
    data_connection = relationship("AccountDataConnection", back_populates="account", uselist=False, cascade="all, delete-orphan")
    
    @property
    def account_admins(self):
        """Returns the list of admin users for this account."""
        return [user for user in self.users if user.is_team_admin]

# Additional indexes for optimization
Index('idx_accounts_created_at', Account.created_at)