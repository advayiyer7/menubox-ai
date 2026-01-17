from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    create_password_reset_token,
    create_verification_token,
    get_current_user,
)
from app.models.user import User
from app.models.preference import Preference
from app.schemas.auth import (
    UserRegister, 
    UserLogin, 
    TokenResponse, 
    UserResponse,
    RefreshTokenRequest,
    AccessTokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    VerifyEmailRequest,
    ResendVerificationRequest,
    MessageResponse,
)
from app.services.email_service import (
    send_password_reset_email,
    send_verification_email,
    send_welcome_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister, 
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    NO TOKENS RETURNED - user must verify email first.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Generate verification token
    verification_token = create_verification_token()
    
    # Create user (NOT verified, NO tokens)
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        email_verified=False,
        reset_token=verification_token,
        reset_token_expires=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    
    try:
        db.add(user)
        db.flush()
        
        # Create default preferences
        preferences = Preference(user_id=user.id)
        db.add(preferences)
        
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Send verification email
    await send_verification_email(user.email, verification_token)
    
    # NO TOKENS - just a message
    return MessageResponse(
        message="Account created! Please check your email to verify your account."
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    BLOCKS if email not verified - returns 403.
    """
    # Find user
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    # Check credentials
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # BLOCK if not verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification link."
        )
    
    # User is verified - generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    device_info = request.headers.get("User-Agent", "Unknown")[:255]
    refresh_token = create_refresh_token(str(user.id), db, device_info)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Get a new access token using a refresh token."""
    refresh_token = verify_refresh_token(data.refresh_token, db)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    access_token = create_access_token(data={"sub": str(refresh_token.user_id)})
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Logout by revoking the refresh token."""
    revoke_refresh_token(data.refresh_token, db)
    return MessageResponse(message="Logged out successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset email."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if user:
        reset_token = create_password_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        await send_password_reset_email(user.email, reset_token)
    
    # Always return success (don't reveal if email exists)
    return MessageResponse(
        message="If an account with that email exists, we sent a password reset link."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using the token from email."""
    user = db.query(User).filter(User.reset_token == data.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    user.password_hash = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    revoke_all_user_tokens(str(user.id), db)
    db.commit()
    
    return MessageResponse(message="Password reset successfully. Please log in.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """Verify email address using the token from email."""
    user = db.query(User).filter(User.reset_token == data.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new one."
        )
    
    # Mark as verified
    user.email_verified = True
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    await send_welcome_email(user.email)
    
    return MessageResponse(message="Email verified successfully! You can now log in.")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """Resend verification email."""
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if user and not user.email_verified:
        verification_token = create_verification_token()
        user.reset_token = verification_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        db.commit()
        await send_verification_email(user.email, verification_token)
    
    return MessageResponse(
        message="If your email is registered and not verified, we sent a new verification link."
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's info."""
    return UserResponse.model_validate(current_user)