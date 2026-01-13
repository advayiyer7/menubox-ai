import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Preference(Base):
    """User food preferences model."""
    
    __tablename__ = "preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    dietary_restrictions = Column(ARRAY(String), default=list)  # vegetarian, vegan, gluten-free, etc.
    favorite_cuisines = Column(ARRAY(String), default=list)  # italian, japanese, mexican, etc.
    disliked_ingredients = Column(ARRAY(String), default=list)  # cilantro, mushrooms, etc.
    spice_preference = Column(String(20), default="medium")  # none, mild, medium, hot, extra_hot
    price_preference = Column(String(20), default="any")  # budget, moderate, upscale, any
    custom_notes = Column(Text, nullable=True)  # Free-form text for additional preferences
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<Preference user_id={self.user_id}>"