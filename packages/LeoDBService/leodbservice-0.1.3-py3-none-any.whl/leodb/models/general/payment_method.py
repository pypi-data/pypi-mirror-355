import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, ForeignKey, CheckConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin

class PaymentMethod(Base, EncryptedModelMixin):
    """
    Represents user payment methods, typically managed via Stripe.
    """
    __tablename__ = "payment_methods"

    _encrypted_fields = [
        'stripe_payment_method_id', 'card_holder_name', 'card_last_four', 'stripe_account_id'
    ]

    # Identifiers
    payment_method_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)

    # Stripe Identifiers (ENCRYPTED)
    stripe_account_id = Column(String)
    stripe_payment_method_id = Column(String)

    # Card Information (partially ENCRYPTED)
    card_holder_name = Column(String)
    card_last_four = Column(String(4)) # Storing only 4 digits, but encrypted for consistency
    card_brand = Column(String(20), nullable=False)
    card_exp_month = Column(String(2), nullable=False)
    card_exp_year = Column(String(4), nullable=False)

    # Status
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_expired = Column(Boolean, nullable=False, default=False, index=True)

    # Stripe Metadata
    stripe_metadata = Column(JSON)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    last_used_at = Column(TIMESTAMP(timezone=True), index=True)

    # Relationships
    account = relationship("Account", back_populates="payment_methods")

    # Constraints
    __table_args__ = (
        CheckConstraint("card_brand IN ('visa', 'mastercard', 'amex', 'discover', 'diners', 'jcb', 'unionpay', 'unknown')", name="payment_methods_card_brand_check"),
        Index('idx_payment_methods_is_expired', 'is_expired'),
    )