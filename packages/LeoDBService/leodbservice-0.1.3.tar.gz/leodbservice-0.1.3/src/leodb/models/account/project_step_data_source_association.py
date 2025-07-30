from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

project_step_data_source_association = Table(
    "project_step_data_source_association",
    Base.metadata,
    Column("project_step_id", UUID(as_uuid=True), ForeignKey("project_step.id", ondelete="CASCADE"), primary_key=True),
    Column("data_source_id", UUID(as_uuid=True), ForeignKey("data_source.id", ondelete="CASCADE"), primary_key=True),
)