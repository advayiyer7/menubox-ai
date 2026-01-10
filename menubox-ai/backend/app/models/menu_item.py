import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class MenuItem(Base):
    """Restaurant menu item model."""
    
    __tablename__ = "menu_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    item_name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2))
    category = Column(String(100))  # appetizer, main, dessert, drink, etc.
    
    # Cached review data
    cached_reviews = Column(JSONB, default=list)
    review_score = Column(Numeric(3, 2))  # 0.00 - 5.00
    mention_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="menu_items")
    
    def __repr__(self):
        return f"<MenuItem {self.item_name}>"
