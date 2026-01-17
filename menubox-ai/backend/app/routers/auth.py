from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

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
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    UserRegister, 
    UserLogin, 
    TokenResponse, 
    UserResponse,
    RefreshTokenRequest,
    AccessTokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePassword,
    VerifyEmailRequest,
    ResendVerificationRequest,
    MessageResponse,
    SessionResponse,
)
from app.services.email_service import (
    send_password_reset_email,
    send_verification_email,
    send_welcome_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Creates user, initializes preferences, and sends verification email.
    Returns JWT tokens on success (but user must verify email to login again).
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
    
    # Create user
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
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Send verification email
    await send_verification_email(user.email, verification_token)
    
    # Generate tokens (user gets one-time access but must verify for future logins)
    access_token = create_access_token(data={"sub": str(user.id)})
    device_info = request.headers.get("User-Agent", "Unknown")[:255]
    refresh_token = create_refresh_token(str(user.id), db, device_info)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    REQUIRES email to be verified before allowing login.
    """
    # Find user
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification link."
        )
    
    # Generate tokens
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
    """
    Get a new access token using a refresh token.
    """
    refresh_token = verify_refresh_token(data.refresh_token, db)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Check if user is still verified (in case admin revokes)
    user = db.query(User).filter(User.id == refresh_token.user_id).first()
    if not user or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified"
        )
    
    # Generate new access token
    access_token = create_access_token(data={"sub": str(refresh_token.user_id)})
    
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout by revoking the refresh token.
    """
    revoke_refresh_token(data.refresh_token, db)
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout from all devices by revoking all refresh tokens.
    """
    count = revoke_all_user_tokens(str(current_user.id), db)
    return MessageResponse(message=f"Logged out from {count} device(s)")


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for the current user.
    """
    sessions = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).order_by(RefreshToken.created_at.desc()).all()
    
    return [
        SessionResponse(
            id=str(session.id),
            device_info=session.device_info or "Unknown device",
            created_at=session.created_at,
            expires_at=session.expires_at,
            is_current=False  # Will be set by frontend based on stored token
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke a specific session by ID.
    """
    session = db.query(RefreshToken).filter(
        RefreshToken.id == session_id,
        RefreshToken.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(session)
    db.commit()
    
    return MessageResponse(message="Session revoked successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.
    
    Always returns success to prevent email enumeration.
    """
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if user:
        # Generate reset token
        reset_token = create_password_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        
        # Send email
        await send_password_reset_email(user.email, reset_token)
    
    # Always return success (security: don't reveal if email exists)
    return MessageResponse(
        message="If an account with that email exists, we sent a password reset link."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using the token from email.
    """
    user = db.query(User).filter(User.reset_token == data.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check expiry
    if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Update password
    user.password_hash = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    # Revoke all refresh tokens (logout everywhere)
    revoke_all_user_tokens(str(user.id), db)
    
    db.commit()
    
    return MessageResponse(message="Password reset successfully. Please log in with your new password.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password while logged in.
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    
    return MessageResponse(message="Password changed successfully")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address using the token from email.
    """
    user = db.query(User).filter(User.reset_token == data.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    # Check expiry
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
    
    # Send welcome email
    await send_welcome_email(user.email)
    
    return MessageResponse(message="Email verified successfully!")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend verification email.
    """
    user = db.query(User).filter(User.email == data.email.lower()).first()
    
    if user and not user.email_verified:
        verification_token = create_verification_token()
        user.reset_token = verification_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        db.commit()
        
        await send_verification_email(user.email, verification_token)
    
    # Always return success
    return MessageResponse(
        message="If your email is registered and not verified, we sent a new verification link."
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's info."""
    return UserResponse.model_validate(current_user)