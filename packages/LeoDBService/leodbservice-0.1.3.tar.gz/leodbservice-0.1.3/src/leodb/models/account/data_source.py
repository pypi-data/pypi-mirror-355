import uuid
import enum
from sqlalchemy import Column, String, TIMESTAMP, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..base import Base
from leodb.encryption.manager import EncryptedModelMixin

class SourceTypeEnum(enum.Enum):
    MCP = "MCP"
    RestAPI = "RestAPI"
    GoogleDrive = "GoogleDrive"
    OneDrive = "OneDrive"

class DataSource(Base, EncryptedModelMixin):
    __tablename__ = "data_source"

    # Define which fields will be transparently encrypted.
    _encrypted_fields = ['connexion_infos']

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(SAEnum(SourceTypeEnum), nullable=False)
    connexion_infos = Column(String, nullable=False)  # This will be encrypted
    shared_access = Column(JSON)
    vector_index_name = Column(String)
    
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())