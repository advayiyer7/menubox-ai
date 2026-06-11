"""
MenuBox AI - FastAPI Backend
Production-ready with health checks and CORS
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.rate_limit import limiter
from app import models  # noqa: F401 - registers all models on Base.metadata
from app.routers import auth, user, menu, recommendations

settings = get_settings()

# Create database tables from the SQLAlchemy models if they don't exist.
# This keeps the schema in sync with the models for both local dev and
# cloud (Neon) without a separate migration step.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MenuBox AI API",
    description="AI-powered restaurant menu recommendations",
    version="1.0.0"
)

# Rate limiting (slowapi). Per-route limits are declared on the routers; this
# registers the limiter instance and the HTTP 429 handler.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
# In production this uses FRONTEND_URL from the environment.
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

allowed_origins = list({
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    frontend_url,
})

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Allow Vercel preview deployments (still requires a valid auth token)
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Health check endpoint (required for Render)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MenuBox AI API",
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(menu.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")