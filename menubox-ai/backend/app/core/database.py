"""
Database configuration - supports local PostgreSQL and Neon (cloud)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

# Use computed URL (handles both local and cloud database)
DATABASE_URL = settings.database_url_computed

# Create engine
# For Neon, we need SSL mode
engine_args = {}
if "neon" in DATABASE_URL or "render" in DATABASE_URL:
    engine_args["connect_args"] = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()