import uuid
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base

# Themes selected by the user
class UserTheme(Base):
    __tablename__ = "user_themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    theme_key = Column(String(50), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="themes")
    indicators = relationship("UserThemeIndicator", back_populates="theme", cascade="all, delete-orphan")
