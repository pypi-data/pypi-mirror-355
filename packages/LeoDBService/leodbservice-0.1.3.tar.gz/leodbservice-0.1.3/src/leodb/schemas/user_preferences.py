import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class UserPreferencesBase(BaseModel):
    language: str = Field("fr", description="User's preferred language ('fr' or 'en')")
    leo_call_name: Optional[str] = Field(None, description="How Leo should address the user")
    agent_tone: str = Field("professional", description="The agent's tone of voice")
    default_currency: str = Field("USD", description="Default currency for financial operations")
    notification_email_enabled: bool = True
    notification_sms_enabled: bool = False
    notification_email: Optional[str] = None # Decrypted on read
    notification_phone: Optional[str] = None # Decrypted on read
    custom_settings: Optional[Dict[str, Any]] = None

class UserPreferencesCreate(UserPreferencesBase):
    user_id: uuid.UUID

class UserPreferencesUpdate(BaseModel):
    language: Optional[str] = None
    leo_call_name: Optional[str] = None
    agent_tone: Optional[str] = None
    default_currency: Optional[str] = None
    notification_email_enabled: Optional[bool] = None
    notification_sms_enabled: Optional[bool] = None
    notification_email: Optional[str] = None
    notification_phone: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None

class UserPreferencesSchema(UserPreferencesBase):
    preference_id: uuid.UUID
    user_id: uuid.UUID

    class Config:
        orm_mode = True