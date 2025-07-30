import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class UserSessionBase(BaseModel):
    client_type: str
    client_version: Optional[str] = None
    client_ip_address: Optional[str] = None # Decrypted on read
    user_agent: Optional[str] = None # Decrypted on read
    metadata: Optional[Dict[str, Any]] = None

class UserSessionCreate(UserSessionBase):
    user_id: uuid.UUID
    jwt_token_hash: str
    expires_at: datetime

class UserSessionSchema(UserSessionBase):
    session_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    is_active: bool

    class Config:
        orm_mode = True