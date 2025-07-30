import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ToolUseSpecBase(BaseModel):
    tool_name: str
    spec: Dict[str, Any]

class ToolUseSpecCreate(ToolUseSpecBase):
    pass

class ToolUseSpecUpdate(BaseModel):
    tool_name: Optional[str] = None
    spec: Optional[Dict[str, Any]] = None

class ToolUseSpecSchema(ToolUseSpecBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True