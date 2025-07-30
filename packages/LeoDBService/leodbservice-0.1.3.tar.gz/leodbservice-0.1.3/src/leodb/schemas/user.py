import uuid
import enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from leodb.models.general.user import UserStatusEnum

class UserBase(BaseModel):
    email: EmailStr
    display_name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    preferred_username: Optional[str] = None
    is_team_admin: bool = False

class UserCreate(UserBase):
    entra_id: str
    tenant_id: Optional[str] = None
    account_id: uuid.UUID
    status: UserStatusEnum = UserStatusEnum.PENDING_TEAM_INVITATION

class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_team_admin: Optional[bool] = None
    status: Optional[UserStatusEnum] = None

class UserSchema(UserBase):
    user_id: uuid.UUID
    entra_id: str
    tenant_id: Optional[str] = None
    account_id: uuid.UUID
    is_active: bool
    status: UserStatusEnum
    created_at: datetime
    last_login_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        orm_mode = True