import uuid
import enum
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

class SourceTypeEnum(str, enum.Enum):
    MCP = "MCP"
    RestAPI = "RestAPI"
    GoogleDrive = "GoogleDrive"
    OneDrive = "OneDrive"

class DataSourceBase(BaseModel):
    source_type: SourceTypeEnum
    connexion_infos: str # This will be the decrypted value on read
    shared_access: Optional[Any] = None
    vector_index_name: Optional[str] = None

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceUpdate(BaseModel):
    source_type: Optional[SourceTypeEnum] = None
    connexion_infos: Optional[str] = None
    shared_access: Optional[Any] = None
    vector_index_name: Optional[str] = None

class DataSourceSchema(DataSourceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True