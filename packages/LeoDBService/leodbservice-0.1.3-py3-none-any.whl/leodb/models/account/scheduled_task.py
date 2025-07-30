import uuid
from sqlalchemy import Column, String, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from .data_source_scheduled_task import data_source_scheduled_task
from .scheduled_task_tool_association import scheduled_task_tool_association

class ScheduledTask(Base):
    __tablename__ = "scheduled_task"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True) # No FK constraint
    prompt = Column(Text, nullable=False)
    
    # Timestamps for scheduling
    date_start = Column(TIMESTAMP(timezone=True), nullable=False)
    date_end = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Recurrence rule conforming to RFC 5545 (iCalendar)
    rrule = Column(String(255))

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    data_sources = relationship("DataSource", secondary=data_source_scheduled_task)
    tools = relationship("ToolUseSpec", secondary=scheduled_task_tool_association)