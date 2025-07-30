import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from leodb.models.base import Base
from leodb.encryption.types import EncryptedString

class AccountDataConnection(Base):
    __tablename__ = "account_data_connections"
    __table_args__ = {"schema": "general"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("general.accounts.id"), nullable=False, index=True
    )
    
    # Connection details
    db_url: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    db_conn_string: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    vector_store_url: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    vector_store_key: Mapped[str] = mapped_column(EncryptedString, nullable=True)

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="data_connection")

    def __repr__(self):
        return f"<AccountDataConnection(id={self.id}, account_id={self.account_id})>"