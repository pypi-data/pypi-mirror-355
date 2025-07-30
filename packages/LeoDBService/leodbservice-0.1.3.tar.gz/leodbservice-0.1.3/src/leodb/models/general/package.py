import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, ForeignKey, CheckConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base

class Package(Base):
    """
    Represents packages/subscriptions held by accounts.
    """
    __tablename__ = "packages"

    # Identifiers
    package_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)

    # Package Type
    package = Column(String(20), nullable=False, default="STANDARD", index=True)  # STANDARD, PRO, ELITE

    # Subscription Period
    begin_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), index=True)
    end_date = Column(TIMESTAMP(timezone=True))  # Optional - null for active subscription

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    account = relationship("Account", back_populates="packages")

    # Constraints
    __table_args__ = (
        CheckConstraint("package IN ('STANDARD', 'PRO', 'ELITE')", name="packages_package_type_check"),
        CheckConstraint("end_date IS NULL OR end_date > begin_date", name="packages_date_range_check"),
    )