import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, ForeignKey, CheckConstraint, Index, Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base

class Invoice(Base):
    """
    Represents monthly subscription invoices.
    """
    __tablename__ = "invoices"

    # Identifiers
    invoice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)

    # Billing Period
    date_from = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    date_to = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    invoice_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    due_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)

    # Package and Plan Details
    package = Column(String(20), nullable=False)
    plan_type = Column(String(20), nullable=False)
    nb_licences = Column(String(10), nullable=False, default="1")

    # Amounts (with 2 decimal places)
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax1_rate = Column(Numeric(5, 4), nullable=False, default=0.0000)
    tax1_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    tax2_rate = Column(Numeric(5, 4), nullable=False, default=0.0000)
    tax2_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    total = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='CAD')

    # Payment
    payment_status = Column(String(20), nullable=False, default='pending', index=True)
    payment_date = Column(TIMESTAMP(timezone=True), index=True)
    payment_confirmation_no = Column(String(100), index=True)
    payment_method_used = Column(String(50))

    # Metadata
    notes = Column(String(1000))
    invoice_metadata = Column("metadata", JSON)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    account = relationship("Account", back_populates="invoices")

    # Constraints
    __table_args__ = (
        CheckConstraint("package IN ('STANDARD', 'PRO', 'ELITE')", name="invoices_package_type_check"),
        CheckConstraint("plan_type IN ('individual', 'team')", name="invoices_plan_type_check"),
        CheckConstraint("payment_status IN ('pending', 'paid', 'failed', 'cancelled', 'refunded')", name="invoices_payment_status_check"),
        CheckConstraint("date_to > date_from", name="invoices_date_range_check"),
        CheckConstraint("due_date >= invoice_date", name="invoices_due_date_check"),
        CheckConstraint("subtotal >= 0 AND total >= 0", name="invoices_amounts_positive_check"),
        Index('idx_invoices_period', 'date_from', 'date_to'),
    )