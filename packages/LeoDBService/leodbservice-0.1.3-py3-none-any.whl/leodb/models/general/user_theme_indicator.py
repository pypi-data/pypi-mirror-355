import uuid
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base

# KPIs selected by the user for a specific theme
class UserThemeIndicator(Base):
    __tablename__ = "user_theme_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_theme_id = Column(UUID(as_uuid=True), ForeignKey("user_themes.id", ondelete="CASCADE"), nullable=False, index=True)
    indicator_key = Column(String(50), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    theme = relationship("UserTheme", back_populates="indicators")