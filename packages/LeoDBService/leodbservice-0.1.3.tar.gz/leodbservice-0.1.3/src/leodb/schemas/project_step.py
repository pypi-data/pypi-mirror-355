import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from leodb.models.account.project_step import ProjectStepStatusEnum
from .data_source import DataSourceSchema
from .tool_use_spec import ToolUseSpecSchema

class ProjectStepBase(BaseModel):
    title: str
    description: Optional[str] = None
    prompt: Optional[str] = None
    output_name: Optional[str] = None
    status: ProjectStepStatusEnum = ProjectStepStatusEnum.PLANNED
    notes: Optional[str] = None

class ProjectStepCreate(ProjectStepBase):
    project_id: uuid.UUID

class ProjectStepUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    output_name: Optional[str] = None
    status: Optional[ProjectStepStatusEnum] = None
    notes: Optional[str] = None

class ProjectStepSchema(ProjectStepBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    data_sources: List[DataSourceSchema] = []
    tools: List[ToolUseSpecSchema] = []

    class Config:
        orm_mode = True