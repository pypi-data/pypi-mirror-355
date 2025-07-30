from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from leodb.models.account.project import ProjectStatusEnum
from .project_step import ProjectStepSchema
from .project_output import ProjectOutputSchema

class ProjectBase(BaseModel):
    prompt: Optional[str] = None
    conversation_history: Optional[str] = None
    status: ProjectStatusEnum = ProjectStatusEnum.PLANNED
    notes: Optional[str] = None

class ProjectCreate(ProjectBase):
    record_id: UUID

class ProjectUpdate(ProjectBase):
    prompt: Optional[str] = None
    conversation_history: Optional[str] = None
    status: Optional[ProjectStatusEnum] = None
    notes: Optional[str] = None

class ProjectSchema(ProjectBase):
    id: UUID
    record_id: UUID
    created_at: datetime
    updated_at: datetime
    project_steps: List[ProjectStepSchema] = []
    outputs: List[ProjectOutputSchema] = []

    class Config:
        orm_mode = True