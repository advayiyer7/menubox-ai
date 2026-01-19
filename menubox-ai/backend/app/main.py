"""
MenuBox AI - FastAPI Backend
Production-ready with health checks and CORS
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, user, menu, recommendations

settings = get_settings()

app = FastAPI(
    title="MenuBox AI API",
    description="AI-powered restaurant menu recommendations",
    version="1.0.0"
)

# CORS Configuration
# In production, this will use FRONTEND_URL from environment
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Allow multiple origins for development and production
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    frontend_url,
]

# Add Vercel preview URLs pattern
if "vercel.app" in frontend_url:
    allowed_origins.append("https://*.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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