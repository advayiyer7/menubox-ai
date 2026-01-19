"""
Application Settings
Supports both local development and production (Render + Neon)
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Database - supports both local and Neon
    # Neon provides DATABASE_URL, local uses individual vars
    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "menubox_ai"
    db_user: str = "postgres"
    db_password: str = ""
    
    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    
    # API Keys
    anthropic_api_key: str | None = None
    google_places_api_key: str | None = None
    yelp_api_key: str | None = None
    
    # Email (Brevo)
    brevo_api_key: str | None = None
    from_email: str = "noreply@menubox.ai"
    from_name: str = "MenuBox AI"
    
    # Frontend URL (for email links)
    frontend_url: str = "http://localhost:5173"
    
    @property
    def database_url_computed(self) -> str:
        """
        Get database URL - prefers DATABASE_URL env var (Neon/Render),
        falls back to constructing from individual vars (local dev).
        """
        # Check for DATABASE_URL (used by Render/Neon)
        db_url = self.database_url or os.getenv("DATABASE_URL")
        
        if db_url:
            # Neon uses postgres:// but SQLAlchemy needs postgresql://
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            return db_url
        
        # Fall back to constructing URL from individual vars
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars


@lru_cache()
def get_settings() -> Settings:
    return Settings()