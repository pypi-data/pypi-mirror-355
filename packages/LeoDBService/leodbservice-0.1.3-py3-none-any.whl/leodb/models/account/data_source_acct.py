import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..base import Base

class DataSourceAcct(Base):
    __tablename__ = "data_source_acct"

    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_source.id", ondelete="CASCADE"), primary_key=True)
    account_id = Column(UUID(as_uuid=True), primary_key=True) # No FK constraint

    data_source = relationship("DataSource")