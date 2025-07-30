import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .data_source import DataSourceSchema
from .tool_use_spec import ToolUseSpecSchema

class ScheduledTaskBase(BaseModel):
    prompt: str
    date_start: datetime
    date_end: Optional[datetime] = None
    rrule: Optional[str] = None

class ScheduledTaskCreate(ScheduledTaskBase):
    user_id: uuid.UUID
    data_source_ids: List[uuid.UUID] = []
    tool_ids: List[uuid.UUID] = []

class ScheduledTaskUpdate(BaseModel):
    prompt: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    rrule: Optional[str] = None
    data_source_ids: Optional[List[uuid.UUID]] = None
    tool_ids: Optional[List[uuid.UUID]] = None

class ScheduledTaskSchema(ScheduledTaskBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    data_sources: List[DataSourceSchema] = []
    tools: List[ToolUseSpecSchema] = []

    class Config:
        orm_mode = True