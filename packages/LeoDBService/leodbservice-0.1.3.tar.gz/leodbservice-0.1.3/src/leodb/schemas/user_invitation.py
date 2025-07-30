import uuid
import enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from leodb.models.general.user_invitation import InvitationStatusEnum

class UserInvitationBase(BaseModel):
    invited_user_email: EmailStr

class UserInvitationCreate(UserInvitationBase):
    account_id: uuid.UUID
    invited_by_user_id: uuid.UUID

class UserInvitationUpdate(BaseModel):
    status: Optional[InvitationStatusEnum] = None

class UserInvitationSchema(UserInvitationBase):
    invitation_id: uuid.UUID
    account_id: uuid.UUID
    invited_by_user_id: uuid.UUID
    invited_user_id: Optional[uuid.UUID] = None
    status: InvitationStatusEnum
    created_at: datetime
    expires_at: datetime

    class Config:
        orm_mode = True