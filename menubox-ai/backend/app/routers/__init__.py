from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.menu import router as menu_router
from app.routers.recommendations import router as recommendations_router

__all__ = [
    "auth_router",
    "user_router",
    "menu_router",
    "recommendations_router",
]
