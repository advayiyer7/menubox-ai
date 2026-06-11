"""
Database configuration - supports local PostgreSQL and Neon (cloud)
"""

from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

# Use computed URL (handles both local and cloud database)
DATABASE_URL = settings.database_url_computed

# Create engine.
# Neon routes to the right compute via SNI, but some psycopg2/libpq builds don't
# send it — so pass the endpoint ID explicitly (https://neon.tech/sni). Also
# require SSL for cloud databases (unless the URL already sets sslmode, which
# psycopg2 errors on if given twice).
connect_args = {}

host = urlparse(DATABASE_URL).hostname or ""
if "neon.tech" in host:
    endpoint_id = host.split(".")[0]  # e.g. ep-plain-tree-at0bpkws
    connect_args["options"] = f"endpoint={endpoint_id}"

if ("neon" in DATABASE_URL or "render" in DATABASE_URL) and "sslmode" not in DATABASE_URL:
    connect_args["sslmode"] = "require"

engine_args = {"connect_args": connect_args} if connect_args else {}
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