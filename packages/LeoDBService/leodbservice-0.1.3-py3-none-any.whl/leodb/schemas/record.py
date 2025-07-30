from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class RecordBase(BaseModel):
    title: Optional[str] = None # Decrypted on read
    description: Optional[str] = None # Decrypted on read
    record_data_entries: Optional[str] = None # Decrypted on read
    record_base_data: Optional[str] = None # Decrypted on read

class RecordCreate(RecordBase):
    user_id: UUID
    conversation_id: Optional[UUID] = None
    record_base_data: Optional[str] = None

class RecordUpdate(RecordBase):
    title: Optional[str] = None
    description: Optional[str] = None
    record_data_entries: Optional[str] = None
    record_base_data: Optional[str] = None

class RecordSchema(RecordBase):
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    projects: List['ProjectSchema'] = []
    data_sources: List['DataSourceSchema'] = []

    class Config:
        orm_mode = True

# Import schemas for forward reference resolution
from .project import ProjectSchema
from .data_source import DataSourceSchema

# Resolve forward references
RecordSchema.model_rebuild()