"""
Pydantic schemas for menu-related API endpoints.
"""

from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


# Request schemas
class RestaurantSearch(BaseModel):
    """Request to search for a restaurant."""
    name: str = Field(..., min_length=1, max_length=255, description="Restaurant name")
    location: Optional[str] = Field(None, max_length=255, description="City, address, or area")


# Alias for the router
RestaurantSearchRequest = RestaurantSearch


class MenuItemCreate(BaseModel):
    """Create a new menu item."""
    item_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None


# Response schemas
class MenuItemResponse(BaseModel):
    """A single menu item."""
    id: UUID
    item_name: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    
    class Config:
        from_attributes = True


class RestaurantResponse(BaseModel):
    """Basic restaurant info."""
    id: UUID
    name: str
    location: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    
    class Config:
        from_attributes = True


class RestaurantWithMenuResponse(BaseModel):
    """Restaurant with menu items - used for search response."""
    id: UUID
    name: str
    location: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    rating: Optional[float] = None
    menu_items: list[MenuItemResponse]
    reviews_analyzed: int = 0
    source: str = "unknown"


# Alias for the router
RestaurantSearchResponse = RestaurantWithMenuResponse


class MenuUploadResponse(BaseModel):
    """Response from menu image upload."""
    restaurant_id: UUID
    restaurant_name: str
    menu_items_count: int
    message: str