import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class PaymentMethodBase(BaseModel):
    """
    Base schema for a payment method.
    """
    card_holder_name: str
    card_brand: str
    card_exp_month: str
    card_exp_year: str
    is_default: bool = False

class PaymentMethodCreate(PaymentMethodBase):
    """
    Schema for creating a new payment method.
    Includes the Stripe token/ID.
    """
    stripe_payment_method_id: str

class PaymentMethodUpdate(BaseModel):
    """
    Schema for updating an existing payment method.
    """
    is_default: Optional[bool] = None

class PaymentMethodSchema(PaymentMethodBase):
    """
    Schema for representing a complete payment method, including its ID.
    Used for API responses.
    """
    payment_method_id: uuid.UUID
    account_id: uuid.UUID
    card_last_four: str # Decrypted on read
    is_active: bool
    is_expired: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        orm_mode = True