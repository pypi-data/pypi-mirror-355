from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class InvoiceBase(BaseModel):
    """
    Base schema for an invoice, reflecting the Invoice model.
    """
    invoice_id: UUID
    account_id: UUID
    invoice_number: str
    date_from: datetime
    date_to: datetime
    invoice_date: datetime
    due_date: datetime
    package: str
    plan_type: str
    nb_licences: str
    subtotal: float
    tax1_rate: float
    tax1_amount: float
    tax2_rate: float
    tax2_amount: float
    total: float
    currency: str
    payment_status: str
    payment_date: Optional[datetime] = None
    payment_confirmation_no: Optional[str] = None
    payment_method_used: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class InvoiceSummarySchema(BaseModel):
    """
    A summarized view of an invoice for list displays.
    """
    invoice_id: UUID
    invoice_number: str
    invoice_date: datetime
    due_date: datetime
    total: float
    currency: str
    payment_status: str

    class Config:
        orm_mode = True

class InvoiceDetailSchema(InvoiceBase):
    """
    Detailed view of an invoice. Currently same as base.
    """
    pass

class PaginatedInvoices(BaseModel):
    """
    Represents a paginated list of invoices.
    """
    page: int
    limit: int
    total_invoices: int
    total_pages: int
    data: List[InvoiceSummarySchema]

class SubscriptionSchema(BaseModel):
    """
    Represents a user's subscription package.
    """
    package_id: UUID
    package: str
    begin_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool

    class Config:
        orm_mode = True