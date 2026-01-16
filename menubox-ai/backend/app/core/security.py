from datetime import datetime, timedelta, timezone
from typing import Any
import secrets
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token (short-lived)."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default: 15 minutes for access tokens
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(user_id: str, db: Session, device_info: str = None) -> str:
    """
    Create a refresh token (long-lived, stored in DB).
    
    Returns the token string.
    """
    # Generate secure token
    token = generate_token(48)
    
    # Set expiry (30 days)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Store in database
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        device_info=device_info
    )
    db.add(refresh_token)
    db.commit()
    
    return token


def verify_refresh_token(token: str, db: Session) -> RefreshToken | None:
    """
    Verify a refresh token and return the token object if valid.
    """
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if not refresh_token:
        return None
    
    if refresh_token.is_expired:
        # Delete expired token
        db.delete(refresh_token)
        db.commit()
        return None
    
    return refresh_token


def revoke_refresh_token(token: str, db: Session) -> bool:
    """Revoke (delete) a refresh token."""
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if refresh_token:
        db.delete(refresh_token)
        db.commit()
        return True
    return False


def revoke_all_user_tokens(user_id: str, db: Session) -> int:
    """Revoke all refresh tokens for a user (logout everywhere)."""
    deleted = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id
    ).delete()
    db.commit()
    return deleted


def create_password_reset_token() -> str:
    """Generate a password reset token."""
    return generate_token(32)


def create_verification_token() -> str:
    """Generate an email verification token."""
    return generate_token(32)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Check token type
    token_type = payload.get("type")
    if token_type != "access":
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get current user only if email is verified."""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox."
        )
    return current_user