from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


# Request schemas
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Request to send password reset email."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ChangePassword(BaseModel):
    """Change password while logged in."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class VerifyEmailRequest(BaseModel):
    """Verify email with token."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email."""
    email: EmailStr


# Response schemas
class UserResponse(BaseModel):
    """User info response."""
    id: UUID
    email: str
    email_verified: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Login/register response with tokens."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds
    user: UserResponse


class AccessTokenResponse(BaseModel):
    """Response for token refresh."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True