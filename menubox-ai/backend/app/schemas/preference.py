from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class SpiceLevel(str, Enum):
    """Spice preference levels."""
    none = "none"
    mild = "mild"
    medium = "medium"
    hot = "hot"
    extra_hot = "extra_hot"


class PricePreference(str, Enum):
    """Price preference levels."""
    budget = "budget"
    moderate = "moderate"
    upscale = "upscale"
    any = "any"


# Request schemas
class PreferenceUpdate(BaseModel):
    """Schema for updating user preferences."""
    dietary_restrictions: list[str] | None = Field(
        default=None,
        description="e.g., vegetarian, vegan, gluten-free, halal, kosher"
    )
    favorite_cuisines: list[str] | None = Field(
        default=None,
        description="e.g., italian, japanese, mexican, indian"
    )
    disliked_ingredients: list[str] | None = Field(
        default=None,
        description="e.g., cilantro, mushrooms, olives"
    )
    spice_preference: SpiceLevel | None = None
    price_preference: PricePreference | None = None


# Response schemas
class PreferenceResponse(BaseModel):
    """Schema for preference responses."""
    id: UUID
    user_id: UUID
    dietary_restrictions: list[str]
    favorite_cuisines: list[str]
    disliked_ingredients: list[str]
    spice_preference: str
    price_preference: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
