import uuid
import enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ContentTypeEnum(str, enum.Enum):
    PDF = "PDF"
    JSON = "JSON"
    MD = "MD"
    CSV = "CSV"

class ProjectOutputBase(BaseModel):
    content_type: ContentTypeEnum
    output_name: Optional[str] = None
    content: Optional[str] = None # Decrypted on read
    notes: Optional[str] = None
    version_number: int

class ProjectOutputCreate(ProjectOutputBase):
    project_id: uuid.UUID
    project_step_id: uuid.UUID

class ProjectOutputUpdate(BaseModel):
    content_type: Optional[ContentTypeEnum] = None
    output_name: Optional[str] = None
    content: Optional[str] = None
    notes: Optional[str] = None
    version_number: Optional[int] = None

class ProjectOutputSchema(ProjectOutputBase):
    id: uuid.UUID
    project_id: uuid.UUID
    project_step_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True