from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class RecommendedItem(BaseModel):
    """A single recommended menu item."""
    item_name: str
    score: int = Field(..., ge=0, le=100, description="Match score 0-100")
    reasoning: str


# Request schemas
class RecommendationRequest(BaseModel):
    """Schema for requesting recommendations."""
    restaurant_id: UUID
    max_items: int = Field(default=5, ge=1, le=10, description="Number of recommendations to return")


# Response schemas
class RecommendationResponse(BaseModel):
    """Schema for recommendation responses."""
    id: UUID
    user_id: UUID
    restaurant_id: UUID | None
    recommended_items: list[RecommendedItem]
    created_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationListResponse(BaseModel):
    """Schema for listing user's recommendation history."""
    recommendations: list[RecommendationResponse]
    total: int
