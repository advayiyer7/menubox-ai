import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recommendation(Base):
    """Generated recommendation history model."""
    
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="SET NULL"))
    
    # Recommendation results
    recommended_items = Column(JSONB, nullable=False)  # [{item_name, score, reasoning}, ...]
    preferences_snapshot = Column(JSONB)  # User preferences at time of recommendation
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
    restaurant = relationship("Restaurant", back_populates="recommendations")
    
    def __repr__(self):
        return f"<Recommendation id={self.id}>"
