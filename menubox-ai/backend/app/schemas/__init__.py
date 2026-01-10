from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    MessageResponse,
)
from app.schemas.preference import (
    PreferenceUpdate,
    PreferenceResponse,
    SpiceLevel,
    PricePreference,
)
from app.schemas.menu import (
    RestaurantSearch,
    MenuItemCreate,
    MenuItemResponse,
    RestaurantResponse,
    RestaurantWithMenuResponse,
    MenuUploadResponse,
)
from app.schemas.recommendation import (
    RecommendedItem,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationListResponse,
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "MessageResponse",
    # Preference
    "PreferenceUpdate",
    "PreferenceResponse",
    "SpiceLevel",
    "PricePreference",
    # Menu
    "RestaurantSearch",
    "MenuItemCreate",
    "MenuItemResponse",
    "RestaurantResponse",
    "RestaurantWithMenuResponse",
    "MenuUploadResponse",
    # Recommendation
    "RecommendedItem",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationListResponse",
]
