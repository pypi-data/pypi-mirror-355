from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

scheduled_task_tool_association = Table(
    "scheduled_task_tool_association",
    Base.metadata,
    Column("scheduled_task_id", UUID(as_uuid=True), ForeignKey("scheduled_task.id", ondelete="CASCADE"), primary_key=True),
    Column("tool_use_spec_id", UUID(as_uuid=True), ForeignKey("tool_use_spec.id", ondelete="CASCADE"), primary_key=True),
)