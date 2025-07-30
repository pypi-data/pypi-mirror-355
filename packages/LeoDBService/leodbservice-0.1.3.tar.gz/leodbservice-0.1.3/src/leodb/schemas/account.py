from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Import User schema for relationship
from .user import UserSchema

class AccountBase(BaseModel):
    """
    Base schema for an account.
    """
    account_name: Optional[str] = Field(None, description="Name of the account or company")
    is_team: bool = Field(False, description="Whether the account is a team account")
    config_admin_email: Optional[str] = Field(None, description="Technical admin email for the account")

class AccountCreate(AccountBase):
    """
    Schema for creating a new account.
    """
    pass

class AccountUpdate(BaseModel):
    """
    Schema for updating an existing account. All fields are optional.
    """
    account_name: Optional[str] = Field(None, description="New name for the account")
    is_team: Optional[bool] = Field(None, description="New account type")
    config_admin_email: Optional[str] = Field(None, description="New technical admin email")

class AccountSchema(AccountBase):
    """
    Complete schema for an account, including database fields.
    Used for reading account data.
    """
    account_id: UUID = Field(..., description="Unique identifier for the account")
    created_at: datetime = Field(..., description="Creation timestamp of the account")
    updated_at: datetime = Field(..., description="Last update timestamp of the account")
    users: List[UserSchema] = Field([], description="List of users associated with this account")

    class Config:
        orm_mode = True