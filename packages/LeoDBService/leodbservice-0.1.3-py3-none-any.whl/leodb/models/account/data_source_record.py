from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base

data_source_record = Table(
    "data_source_record",
    Base.metadata,
    Column("record_id", UUID(as_uuid=True), ForeignKey("record.id", ondelete="CASCADE"), primary_key=True),
    Column("data_source_id", UUID(as_uuid=True), ForeignKey("data_source.id", ondelete="CASCADE"), primary_key=True),
)