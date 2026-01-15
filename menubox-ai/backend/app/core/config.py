from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_env: str = "development"
    debug: bool = True
    app_name: str = "MenuBox AI"
    api_prefix: str = "/api"
    
    # Database
    database_url: str
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days
    
    # AI Services
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    
    # External APIs
    google_places_api_key: str | None = None
    yelp_api_key: str | None = None
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    # In the Settings class, add:
    yelp_api_key: str | None = None


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()