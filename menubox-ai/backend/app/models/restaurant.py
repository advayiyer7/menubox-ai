import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Restaurant(Base):
    """Restaurant information model."""
    
    __tablename__ = "restaurants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    location = Column(String(255))
    cuisine_type = Column(String(100))
    price_range = Column(String(10))  # $, $$, $$$, $$$$
    yelp_id = Column(String(100))
    google_place_id = Column(String(100))
    last_scraped = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="restaurant")
    
    def __repr__(self):
        return f"<Restaurant {self.name}>"